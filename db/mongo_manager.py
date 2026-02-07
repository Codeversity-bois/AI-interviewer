"""MongoDB manager for storing interview results and evaluations."""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "zenith_interviews")

_client = None
_db = None


def _get_db():
    """Lazy-init MongoDB connection."""
    global _client, _db
    if _db is not None:
        return _db

    try:
        from pymongo import MongoClient
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Quick connectivity check
        _client.server_info()
        _db = _client[MONGO_DB_NAME]
        print(f"Connected to MongoDB: {MONGO_DB_NAME}")
        return _db
    except Exception as e:
        print(f"Warning: MongoDB not available: {e}")
        return None


def save_interview_result(result: Dict[str, Any]) -> Optional[str]:
    """Save a complete interview result (session + transcript + evaluation) to MongoDB.

    Args:
        result: The full interview result dict from InterviewOrchestrator.end_interview().

    Returns:
        The inserted document's _id as a string, or None on failure.
    """
    db = _get_db()
    if db is None:
        print("[MongoDB] Skipping save — not connected")
        return None

    doc = {
        "saved_at": datetime.utcnow().isoformat(),
        **result,
    }

    try:
        inserted = db.interview_results.insert_one(doc)
        print(f"[MongoDB] Saved interview result: {inserted.inserted_id}")
        return str(inserted.inserted_id)
    except Exception as e:
        print(f"[MongoDB] Error saving result: {e}")
        return None


def save_qa_evaluation(session_id: str, qa_pair: Dict[str, Any]) -> Optional[str]:
    """Save a single Q&A evaluation (question, answer, interviewer evaluation).

    Args:
        session_id: The interview session ID.
        qa_pair: Dict with question, answer, evaluation fields.

    Returns:
        Inserted _id as string, or None on failure.
    """
    db = _get_db()
    if db is None:
        return None

    doc = {
        "session_id": session_id,
        "saved_at": datetime.utcnow().isoformat(),
        **qa_pair,
    }

    try:
        inserted = db.qa_evaluations.insert_one(doc)
        return str(inserted.inserted_id)
    except Exception as e:
        print(f"[MongoDB] Error saving Q&A evaluation: {e}")
        return None


def get_interview_result(session_id: str) -> Optional[Dict]:
    """Retrieve an interview result by session_id."""
    db = _get_db()
    if db is None:
        return None

    try:
        doc = db.interview_results.find_one({"session.session_id": session_id}, {"_id": 0})
        return doc
    except Exception as e:
        print(f"[MongoDB] Error retrieving result: {e}")
        return None
