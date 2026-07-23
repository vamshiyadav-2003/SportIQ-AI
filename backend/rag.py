"""
rag.py
------
The actual Retrieval-Augmented Generation pipeline:
1. pull relevant chunks from ChromaDB (local knowledge)
2. pull a few fresh snippets from the web (recent news/stats)
3. merge them into a single context list that gets handed to the LLM
"""

import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


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
            print(f"[rag] Fallback error reading {file_path}: {e}")

    return []


def get_rag_context(sport: str, difficulty: str) -> dict:
    local_chunks = retrieve_local_file_context(sport=sport, n_results=3)
    web_chunks = []

    combined = local_chunks

    if not combined:
        combined = [
            f"No indexed knowledge found for '{sport}'. "
            f"Generate general, well-known {difficulty} level questions about {sport}, "
            f"but state clearly this is general knowledge and not sourced context."
        ]

    return {
        "context": combined,
        "local": local_chunks,
        "web": web_chunks
    }
