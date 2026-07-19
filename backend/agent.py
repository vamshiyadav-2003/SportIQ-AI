"""
agent.py
--------
The AI Agent layer:
- Fetches RAG context (ChromaDB + Tavily web search)
- Builds prompt templates
- Invokes Groq LLM with automatic model fallback
- Cleans and validates JSON output format for frontend display
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
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
FALLBACK_MODELS = ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"]

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here" else None


def _strip_code_fences(text: str) -> str:
    """Removes markdown code fences and extraneous text outside JSON structure."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    
    # Extract JSON object if embedded in text
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    return text


def _call_groq_with_fallback(messages: list) -> str:
    """Invokes Groq completion trying primary model then fallbacks."""
    models_to_try = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_err = None

    for model in models_to_try:
        try:
            completion = _client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=1500,
            )
            content = completion.choices[0].message.content
            if content and content.strip():
                return content
        except Exception as e:
            print(f"[agent] Groq model '{model}' failed: {e}")
            last_err = e

    raise RuntimeError(f"All Groq models failed to generate response. Error: {last_err}")


def generate_quiz(sport: str, difficulty: str) -> dict:
    if _client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Please set a valid GROQ_API_KEY in backend/.env file."
        )

    rag_data = get_rag_context(sport, difficulty)
    context_chunks = rag_data.get("context", [])
    user_prompt = build_quiz_user_prompt(sport, difficulty, context_chunks)

    messages = [
        {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw_text = _call_groq_with_fallback(messages)
    cleaned = _strip_code_fences(raw_text)

    try:
        quiz_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response could not be parsed as JSON: {raw_text[:250]}...") from e

    # Validation and formatting
    quiz_json["sport"] = sport
    quiz_json["difficulty"] = difficulty
    quiz_json["sources"] = {
        "local": rag_data.get("local", []),
        "web": rag_data.get("web", [])
    }

    questions = quiz_json.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("AI response did not contain a valid 'questions' list.")

    # Sanitize each question
    sanitized_questions = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        question_text = q.get("question", "Question text missing")
        options = q.get("options", {})
        if not isinstance(options, dict) or len(options) < 2:
            options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
        answer = str(q.get("answer", "A")).upper().strip()
        if answer not in options:
            answer = list(options.keys())[0]
        explanation = q.get("explanation", "Explanation unavailable.")

        sanitized_questions.append({
            "question": question_text,
            "options": options,
            "answer": answer,
            "explanation": explanation
        })

    quiz_json["questions"] = sanitized_questions
    return quiz_json
