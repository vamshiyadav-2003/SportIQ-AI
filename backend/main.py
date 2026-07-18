"""
main.py
-------
FastAPI entrypoint for SportIQ AI.

Endpoints:
    POST /generate-quiz   -> generate a new quiz (RAG + web search + LLM)
    GET  /quiz-history     -> list previously generated quizzes
    GET  /health           -> simple health check
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import generate_quiz
from chroma_store import build_index_if_needed

app = FastAPI(title="SportIQ AI", version="1.0.0")

# Frontend runs on a different port during development, so CORS needs to be open.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "quiz_history.db"


class QuizRequest(BaseModel):
    sport: str
    difficulty: str


def _init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO quiz_history (sport, difficulty, questions, created_at) VALUES (?, ?, ?, ?)",
            (sport, difficulty, json.dumps(questions), datetime.utcnow().isoformat()),
        )
        conn.commit()


@app.on_event("startup")
def on_startup():
    _init_db()
    build_index_if_needed()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-quiz")
def generate_quiz_route(payload: QuizRequest):
    sport = payload.sport.strip()
    difficulty = payload.difficulty.strip().lower()

    if not sport:
        raise HTTPException(status_code=400, detail="Sport is required.")
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(status_code=400, detail="Difficulty must be easy, medium, or hard.")

    try:
        quiz = generate_quiz(sport, difficulty)
    except RuntimeError as e:
        # missing API key etc - not a server bug, tell the user how to fix it
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {e}")

    _save_to_history(sport, difficulty, quiz["questions"])
    return quiz


@app.get("/quiz-history")
def quiz_history(limit: int = 20):
    with closing(sqlite3.connect(DB_PATH)) as conn:
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

# Serve React frontend static files in production
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/build"))
if os.path.exists(BUILD_DIR):
    app.mount("/", StaticFiles(directory=BUILD_DIR, html=True), name="static")
