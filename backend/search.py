"""
search.py
---------
Wraps the Tavily search API so the agent can pull in recent sports
news/stats that wouldn't be in the local ChromaDB knowledge base
(e.g. "who won the 2026 T20 World Cup").

If no TAVILY_API_KEY is set, this module quietly returns an empty
list instead of crashing, so the app still works in RAG-only mode.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def web_search_snippets(sport: str, difficulty: str, max_results: int = 4):
    """
    Search the web for recent info about a sport and return a list of
    short text snippets that can be appended to the RAG context.
    """
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        # No key configured - skip web search, rely on local knowledge base only.
        return []

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=TAVILY_API_KEY)
        query = f"latest {sport} records, statistics and results relevant to a {difficulty} difficulty quiz"

        response = client.search(query=query, max_results=max_results, search_depth="basic")

        snippets = []
        for result in response.get("results", []):
            content = result.get("content", "").strip()
            if content:
                snippets.append(content[:600])  # keep snippets short

        return snippets

    except Exception as e:
        print(f"[search] Web search failed, continuing without it: {e}")
        return []
