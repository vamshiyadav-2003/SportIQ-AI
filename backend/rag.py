"""
rag.py
------
The actual Retrieval-Augmented Generation pipeline:
1. pull relevant chunks from ChromaDB (local knowledge)
2. pull a few fresh snippets from the web (recent news/stats)
3. merge them into a single context list that gets handed to the LLM
"""

from chroma_store import retrieve_context
from search import web_search_snippets


def get_rag_context(sport: str, difficulty: str) -> list[str]:
    query = f"{sport} facts records statistics {difficulty} quiz questions"

    local_chunks = retrieve_context(sport=sport, query=query, n_results=5)
    web_chunks = web_search_snippets(sport=sport, difficulty=difficulty)

    combined = local_chunks + web_chunks

    if not combined:
        combined = [
            f"No indexed knowledge found for '{sport}'. "
            f"Generate general, well-known {difficulty} level questions about {sport}, "
            f"but state clearly this is general knowledge and not sourced context."
        ]

    return combined
