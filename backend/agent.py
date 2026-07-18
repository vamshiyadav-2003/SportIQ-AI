"""
agent.py
--------
The "agent" layer. This is intentionally kept small: it decides what
context to pull (via rag.py), builds the prompt (via prompts.py), calls
the LLM, and parses the result into the JSON shape the frontend expects.
"""

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from prompts import QUIZ_SYSTEM_PROMPT, build_quiz_user_prompt
from rag import get_rag_context

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here" else None


def _strip_code_fences(text: str) -> str:
    """LLMs love wrapping JSON in ```json fences even when told not to. Strip them."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def generate_quiz(sport: str, difficulty: str) -> dict:
    if _client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your Groq API key before calling /generate-quiz."
        )

    rag_data = get_rag_context(sport, difficulty)
    context_chunks = rag_data["context"]
    user_prompt = build_quiz_user_prompt(sport, difficulty, context_chunks)

    completion = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
        max_tokens=1500,
    )

    raw_text = completion.choices[0].message.content
    cleaned = _strip_code_fences(raw_text)

    try:
        quiz_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model did not return valid JSON, got: {raw_text[:300]}..."
        ) from e

    # basic shape check so the frontend doesn't choke on a malformed response
    quiz_json.setdefault("sport", sport)
    quiz_json.setdefault("difficulty", difficulty)
    quiz_json["sources"] = {
        "local": rag_data["local"],
        "web": rag_data["web"]
    }
    if "questions" not in quiz_json or not isinstance(quiz_json["questions"], list):
        raise ValueError("Model response missing a valid 'questions' list.")

    return quiz_json
