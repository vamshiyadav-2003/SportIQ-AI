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
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_store")

COLLECTION_NAME = "sports_quiz_database"

# Use ChromaDB's built-in DefaultEmbeddingFunction (ONNX-based all-MiniLM-L6-v2).
# This runs locally with ~50MB RAM — well within Render Free tier's 512MB limit.
# No PyTorch, no external API calls, no network dependency during startup.
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_embedding_fn = DefaultEmbeddingFunction()
print("[chroma_store] Using ChromaDB DefaultEmbeddingFunction (ONNX, local, no network required).")


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
