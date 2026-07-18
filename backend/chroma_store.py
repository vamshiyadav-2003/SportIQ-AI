"""
chroma_store.py
----------------
Handles everything related to the ChromaDB vector database:
- building the collection from the /data text files on first run
- loading the persistent collection on later runs
- running similarity search for a given sport + query

I kept this separate from rag.py so the "database plumbing" is not
mixed in with the actual retrieval/prompting logic.
"""

import os
from pathlib import Path

import chromadb
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_store")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

COLLECTION_NAME = "sports_quiz_database"

class HuggingFaceServerlessEmbeddings(EmbeddingFunction):
    def __init__(self, api_key: str = None, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.api_url = f"https://router.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def __call__(self, input: Documents) -> Embeddings:
        import requests
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": input, "options": {"wait_for_model": True}}
        )
        if response.status_code != 200:
            raise ValueError(f"Hugging Face API returned error ({response.status_code}): {response.text}")
        return response.json()

_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Hybrid Embedding Function:
# - On Render (Production): Use HuggingFace Serverless API to avoid OOM (Out Of Memory) errors.
# - In local development (Offline sandbox): Fall back to local SentenceTransformer.
_embedding_fn = None
if not os.getenv("RENDER"):
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        _embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        print("[chroma_store] Using local SentenceTransformer (offline sandbox fallback).")
    except ImportError:
        pass

if _embedding_fn is None:
    hf_token = os.getenv("HF_API_KEY", "")
    _embedding_fn = HuggingFaceServerlessEmbeddings(
        api_key=hf_token if hf_token else None,
        model_name=EMBEDDING_MODEL
    )
    print("[chroma_store] Using HuggingFace Serverless API embedding function (router.huggingface.co).")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """Very simple sliding-window chunker. Good enough for small .txt files."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def get_collection():
    """Get (or create) the sports_quiz_database collection."""
    return _client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=_embedding_fn
    )


def build_index_if_needed():
    """
    On first run, read every .txt file in /data and load it into Chroma.
    If the collection already has documents, skip re-indexing.
    """
    collection = get_collection()
    if collection.count() > 0:
        print(f"[chroma_store] Collection already has {collection.count()} chunks, skipping rebuild.")
        return collection

    print("[chroma_store] Building vector index from /data ...")
    doc_id = 0
    for file_path in DATA_DIR.glob("*.txt"):
        sport = file_path.stem.lower()
        raw_text = file_path.read_text(encoding="utf-8")

        for chunk in _chunk_text(raw_text):
            collection.add(
                ids=[f"{sport}-{doc_id}"],
                documents=[chunk],
                metadatas=[{"sport": sport}],
            )
            doc_id += 1

    print(f"[chroma_store] Indexed {doc_id} chunks across {len(list(DATA_DIR.glob('*.txt')))} files.")
    return collection


def retrieve_context(sport: str, query: str, n_results: int = 5):
    """
    Run a similarity search scoped to the requested sport.
    Falls back to an unfiltered search if nothing matches the sport filter
    (e.g. sport name in the file doesn't exactly match the dropdown value).
    """
    collection = get_collection()
    sport = sport.lower().strip()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"sport": sport},
    )

    documents = results.get("documents", [[]])[0]

    if not documents:
        # fallback: no metadata filter
        results = collection.query(query_texts=[query], n_results=n_results)
        documents = results.get("documents", [[]])[0]

    return documents
