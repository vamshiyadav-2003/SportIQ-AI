"""
main.py
-------
FastAPI entrypoint for SportIQ AI.

Endpoints:
    POST /generate-quiz   -> generate a new quiz (RAG + web search + LLM)
    GET  /quiz-history     -> list previously generated quizzes
    GET  /health           -> detailed system & database health check
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import generate_quiz
from chroma_store import build_index_if_needed, get_collection

app = FastAPI(title="SportIQ AI", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).resolve().parent / "quiz_history.db"


class QuizRequest(BaseModel):
    sport: str
    difficulty: str


def _init_db():
    with closing(sqlite3.connect(str(DB_PATH))) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _save_to_history(sport: str, difficulty: str, questions: list):
    with closing(sqlite3.connect(str(DB_PATH))) as conn:
        conn.execute(
            "INSERT INTO quiz_history (sport, difficulty, questions, created_at) VALUES (?, ?, ?, ?)",
            (sport, difficulty, json.dumps(questions), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


@app.on_event("startup")
def on_startup():
    _init_db()
    try:
        build_index_if_needed()
    except Exception as e:
        print(f"[startup] Notice: ChromaDB vector store check deferred/failed: {e}")


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SportIQ AI Backend API",
        "version": "1.0.0",
        "health": "/health",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    db_ok = DB_PATH.exists()
    doc_count = 0
    try:
        collection = get_collection()
        if collection:
            doc_count = collection.count()
    except Exception:
        pass

    return {
        "status": "ok",
        "database": "connected" if db_ok else "initialized",
        "vector_store": {
            "indexed_documents": doc_count,
            "status": "active" if doc_count > 0 else "fallback_mode"
        }
    }


@app.post("/generate-quiz")
def generate_quiz_route(payload: QuizRequest):
    sport = payload.sport.strip()
    difficulty = payload.difficulty.strip().lower()

    if not sport:
        raise HTTPException(status_code=400, detail="Sport parameter is required.")
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(status_code=400, detail="Difficulty must be easy, medium, or hard.")

    try:
        quiz = generate_quiz(sport, difficulty)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"AI model returned an unusable format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected backend error: {e}")

    try:
        _save_to_history(sport, difficulty, quiz.get("questions", []))
    except Exception as e:
        print(f"[main] Failed to save quiz to history DB: {e}")

    return quiz


@app.get("/quiz-history")
def quiz_history(limit: int = 20):
    if not DB_PATH.exists():
        return []

    try:
        with closing(sqlite3.connect(str(DB_PATH))) as conn:
            rows = conn.execute(
                "SELECT id, sport, difficulty, questions, created_at FROM quiz_history "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            {
                "id": r[0],
                "sport": r[1],
                "difficulty": r[2],
                "questions": json.loads(r[3]),
                "created_at": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[main] Error reading quiz history: {e}")
        return []


# Serve React frontend static build in production if available
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/build"))
if os.path.exists(BUILD_DIR):
    app.mount("/", StaticFiles(directory=BUILD_DIR, html=True), name="static")
