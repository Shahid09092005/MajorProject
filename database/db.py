import sqlite3
import json
import numpy as np
from datetime import datetime
from config import DB_PATH


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT NOT NULL,
            structured_data TEXT NOT NULL,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            structured_data TEXT NOT NULL,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            resume_id INTEGER NOT NULL,
            match_score REAL NOT NULL,
            semantic_similarity REAL,
            result_data TEXT NOT NULL,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gap_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            gap_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES match_results(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            questions_answers TEXT NOT NULL,
            overall_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES match_results(id)
        )
    """)

    conn.commit()
    conn.close()


# --------------- Embedding helpers ---------------

def serialize_embedding(embedding: np.ndarray) -> bytes:
    return embedding.astype(np.float32).tobytes()


def deserialize_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


# --------------- Jobs ---------------

def save_job(raw_text: str, structured_data: dict, embedding: np.ndarray = None) -> int:
    conn = _get_connection()
    emb_blob = serialize_embedding(embedding) if embedding is not None else None
    cursor = conn.execute(
        "INSERT INTO jobs (raw_text, structured_data, embedding) VALUES (?, ?, ?)",
        (raw_text, json.dumps(structured_data), emb_blob),
    )
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id


def get_job(job_id: int) -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_latest_job() -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# --------------- Resumes ---------------

def save_resume(filename: str, raw_text: str, structured_data: dict, embedding: np.ndarray = None) -> int:
    conn = _get_connection()
    emb_blob = serialize_embedding(embedding) if embedding is not None else None
    cursor = conn.execute(
        "INSERT INTO resumes (filename, raw_text, structured_data, embedding) VALUES (?, ?, ?, ?)",
        (filename, raw_text, json.dumps(structured_data), emb_blob),
    )
    conn.commit()
    resume_id = cursor.lastrowid
    conn.close()
    return resume_id


def get_resume(resume_id: int) -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_latest_resume() -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM resumes ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# --------------- Match Results ---------------

def save_match_result(job_id: int, resume_id: int, match_score: float,
                      semantic_similarity: float, result_data: dict, explanation: str) -> int:
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO match_results (job_id, resume_id, match_score, semantic_similarity, result_data, explanation) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, resume_id, match_score, semantic_similarity, json.dumps(result_data), explanation),
    )
    conn.commit()
    match_id = cursor.lastrowid
    conn.close()
    return match_id


def get_match_result(match_id: int) -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM match_results WHERE id = ?", (match_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_latest_match() -> dict | None:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM match_results ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# --------------- Gap Analyses ---------------

def save_gap_analysis(match_id: int, gap_data: dict) -> int:
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO gap_analyses (match_id, gap_data) VALUES (?, ?)",
        (match_id, json.dumps(gap_data)),
    )
    conn.commit()
    gap_id = cursor.lastrowid
    conn.close()
    return gap_id


def get_gap_analysis(match_id: int) -> dict | None:
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM gap_analyses WHERE match_id = ? ORDER BY id DESC LIMIT 1",
        (match_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# --------------- Interview Sessions ---------------

def save_interview_session(match_id: int, questions_answers: list, overall_score: float) -> int:
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO interview_sessions (match_id, questions_answers, overall_score) VALUES (?, ?, ?)",
        (match_id, json.dumps(questions_answers), overall_score),
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def get_interview_session(match_id: int) -> dict | None:
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM interview_sessions WHERE match_id = ? ORDER BY id DESC LIMIT 1",
        (match_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# --------------- Helpers ---------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("structured_data", "result_data", "gap_data", "questions_answers"):
        if key in d and isinstance(d[key], str):
            d[key] = json.loads(d[key])
    if "embedding" in d and d["embedding"] is not None:
        d["embedding"] = deserialize_embedding(d["embedding"])
    return d
