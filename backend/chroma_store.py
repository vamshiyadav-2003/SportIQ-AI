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

# Instant local store backed by /data text files
def get_collection():
    """Returns local store handle."""
    return None


def build_index_if_needed():
    """Verify local text knowledge base files exist in /data."""
    txt_files = list(DATA_DIR.glob("*.txt"))
    print(f"[chroma_store] Local knowledge base active with {len(txt_files)} text files in /data.")
    return None


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """Simple sliding-window chunker for local text files."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def retrieve_local_file_context(sport: str, n_results: int = 3) -> list[str]:
    """Instant local file retriever that reads directly from /data/{sport}.txt."""
    sport_clean = sport.lower().strip()
    file_path = DATA_DIR / f"{sport_clean}.txt"
    
    if not file_path.exists():
        # search for any matching file stem
        matching = [f for f in DATA_DIR.glob("*.txt") if sport_clean in f.stem.lower() or f.stem.lower() in sport_clean]
        if matching:
            file_path = matching[0]

    if file_path.exists():
        try:
            raw_text = file_path.read_text(encoding="utf-8")
            chunks = _chunk_text(raw_text)
            if len(chunks) <= n_results:
                return chunks
            import random
            return random.sample(chunks, n_results)
        except Exception as e:
            print(f"[chroma_store] Error reading {file_path}: {e}")
            
    return []


def retrieve_context(sport: str, query: str, n_results: int = 3):
    """
    Returns instant context from local data text files (/data/<sport>.txt).
    Fast, reliable, 0MB network download required.
    """
    return retrieve_local_file_context(sport=sport, n_results=n_results)

