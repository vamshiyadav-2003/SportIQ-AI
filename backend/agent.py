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

PRIMARY_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODELS = ["llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"]


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        return None
    return Groq(api_key=api_key)


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


def _extract_partial_questions(text: str) -> list:
    """Extracts valid individual question objects from a truncated JSON string."""
    pattern = r'\{\s*"question"\s*:\s*".*?"\s*,\s*"options"\s*:\s*\{.*?\}\s*,\s*"answer"\s*:\s*".*?"\s*,\s*"explanation"\s*:\s*".*?"\s*\}'
    matches = re.findall(pattern, text, re.DOTALL)
    results = []
    for m in matches:
        try:
            results.append(json.loads(m))
        except Exception:
            pass
    return results


def _call_groq_with_fallback(messages: list, client: Groq) -> str:
    """Invokes Groq completion trying primary model then fallbacks."""
    primary_model = os.getenv("GROQ_MODEL", PRIMARY_MODEL)
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]
    last_err = None

    for model in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=2500,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            if content and content.strip():
                return content
        except Exception as e:
            print(f"[agent] Groq model '{model}' failed: {e}")
            last_err = e

    raise RuntimeError(f"All Groq models failed to generate response. Error: {last_err}")


def generate_quiz(sport: str, difficulty: str) -> dict:
    client = get_groq_client()
    if client is None:
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

    raw_text = _call_groq_with_fallback(messages, client)
    cleaned = _strip_code_fences(raw_text)

    quiz_json = None
    try:
        quiz_json = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_partial_questions(cleaned)
        if extracted and len(extracted) > 0:
            quiz_json = {"questions": extracted}
        else:
            try:
                raw_retry = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2500,
                    response_format={"type": "json_object"},
                ).choices[0].message.content
                quiz_json = json.loads(_strip_code_fences(raw_retry))
            except Exception as e:
                raise ValueError(f"Model did not return valid JSON: {cleaned[:150]}...") from e

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
