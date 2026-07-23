"""
rag.py
------
The actual Retrieval-Augmented Generation pipeline:
1. pull relevant chunks from ChromaDB (local knowledge)
2. pull a few fresh snippets from the web (recent news/stats)
3. merge them into a single context list that gets handed to the LLM
"""

from chroma_store import retrieve_local_file_context


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
