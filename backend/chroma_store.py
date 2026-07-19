"""
chroma_store.py
----------------
Handles vector database persistent indexing and similarity search using ChromaDB:
- Auto-indexes local sports knowledge files from /data/*.txt on startup into a vector collection
- Queries vector similarity embeddings with sport metadata filtering
- Provides reliable local chunk fallback if vector store yields insufficient items
"""

import os
import random
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Silence ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings

# Silence internal Chroma telemetry events dynamically without triggering IDE linter import errors
_posthog = sys.modules.get("posthog")
if _posthog and hasattr(_posthog, "capture"):
    setattr(_posthog, "capture", lambda *args, **kwargs: None)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_store")
COLLECTION_NAME = "sports_quiz_database"

_client = None
_collection = None


def get_client():
    global _client
    if _client is None:
        settings = Settings(anonymized_telemetry=False)
        try:
            _client = chromadb.PersistentClient(path=CHROMA_PATH, settings=settings)
        except Exception as e:
            print(f"[chroma_store] PersistentClient warning ({e}), falling back to in-memory Client.")
            _client = chromadb.Client(settings=settings)

        # Patch capture on client load if posthog was loaded by chromadb
        _ph = sys.modules.get("posthog")
        if _ph and hasattr(_ph, "capture"):
            setattr(_ph, "capture", lambda *args, **kwargs: None)

    return _client


def get_collection():
    global _collection
    if _collection is not None:
        return _collection

    client = get_client()
    try:
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"[chroma_store] Error getting or creating collection: {e}")
        _collection = None
    return _collection


def _chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    """Splits raw text into paragraph/sentence aware chunks for optimal indexing."""
    chunks = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    current_chunk = []
    current_length = 0

    for line in lines:
        if current_length + len(line) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c.strip() for c in chunks if len(c.strip()) > 20]


def build_index_if_needed():
    """Verify and populate the ChromaDB vector database from text files in /data."""
    collection = get_collection()
    if collection is None:
        print("[chroma_store] Warning: ChromaDB collection unavailable.")
        return None

    try:
        count = collection.count()
        if count > 0:
            print(f"[chroma_store] ChromaDB collection '{COLLECTION_NAME}' ready with {count} indexed documents.")
            return count
    except Exception as e:
        print(f"[chroma_store] Could not check doc count: {e}")

    txt_files = list(DATA_DIR.glob("*.txt"))
    if not txt_files:
        print("[chroma_store] No text files found in /data directory.")
        return 0

    documents = []
    metadatas = []
    ids = []

    for f in txt_files:
        sport_name = f.stem.lower().strip()
        try:
            raw_text = f.read_text(encoding="utf-8")
            chunks = _chunk_text(raw_text)
            for i, chunk in enumerate(chunks):
                doc_id = f"{sport_name}_{i}"
                documents.append(chunk)
                metadatas.append({"sport": sport_name, "source": f.name, "chunk_index": i})
                ids.append(doc_id)
        except Exception as e:
            print(f"[chroma_store] Failed reading {f.name}: {e}")

    if documents:
        try:
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                collection.upsert(
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                    ids=ids[i : i + batch_size]
                )
            print(f"[chroma_store] Indexed {len(documents)} document chunks from {len(txt_files)} files into ChromaDB.")
            return len(documents)
        except Exception as e:
            print(f"[chroma_store] Error populating ChromaDB index: {e}")

    return 0


def retrieve_local_file_context(sport: str, n_results: int = 3) -> list[str]:
    """Fallback text chunk retriever reading directly from /data/{sport}.txt."""
    sport_clean = sport.lower().strip()
    file_path = DATA_DIR / f"{sport_clean}.txt"

    if not file_path.exists():
        matching = [f for f in DATA_DIR.glob("*.txt") if sport_clean in f.stem.lower() or f.stem.lower() in sport_clean]
        if matching:
            file_path = matching[0]

    if file_path.exists():
        try:
            raw_text = file_path.read_text(encoding="utf-8")
            chunks = _chunk_text(raw_text)
            if len(chunks) <= n_results:
                return chunks
            return random.sample(chunks, n_results)
        except Exception as e:
            print(f"[chroma_store] Fallback error reading {file_path}: {e}")

    return []


def retrieve_context(sport: str, query: str, n_results: int = 3) -> list[str]:
    """
    Performs similarity search using ChromaDB vector database.
    Falls back to direct local file chunking if ChromaDB returns no results.
    """
    sport_clean = sport.lower().strip()
    collection = get_collection()

    if collection is not None:
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"sport": sport_clean}
            )
            docs = results.get("documents", [[]])[0]
            if docs and len(docs) > 0:
                return docs
        except Exception as e:
            print(f"[chroma_store] Chroma vector query with filter error: {e}")

        try:
            results = collection.query(
                query_texts=[f"{sport} {query}"],
                n_results=n_results
            )
            docs = results.get("documents", [[]])[0]
            if docs and len(docs) > 0:
                return docs
        except Exception as e:
            print(f"[chroma_store] Chroma general vector query error: {e}")

    return retrieve_local_file_context(sport=sport, n_results=n_results)
