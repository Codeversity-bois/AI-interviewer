"""Candidate profile ingestion and AstraDB vector storage."""

from datetime import datetime
from typing import List, Optional, Dict

from live_interview_service.config import (
    ASTRA_DB_TOKEN, ASTRA_DB_ENDPOINT, CANDIDATE_COLLECTION,
)
from live_interview_service.models import CandidateInput

# ── AstraDB connection ────────────────────────────────────────────────────────

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    if not ASTRA_DB_TOKEN or not ASTRA_DB_ENDPOINT:
        print("[CandidateStore] AstraDB credentials not set — running in memory-only mode")
        return None

    try:
        from astrapy import DataAPIClient
        from astrapy.constants import VectorMetric

        client = DataAPIClient(ASTRA_DB_TOKEN)
        db = client.get_database_by_api_endpoint(ASTRA_DB_ENDPOINT)
        
        # Check if collection exists, if not create it
        try:
             _collection = db.get_collection(CANDIDATE_COLLECTION)
             print(f"[CandidateStore] Connected to AstraDB collection: {CANDIDATE_COLLECTION}")
        except Exception:
             print(f"[CandidateStore] Collection '{CANDIDATE_COLLECTION}' not found. Creating...")
             _collection = db.create_collection(
                 CANDIDATE_COLLECTION,
                 dimension=768,  # MPNet dimension
                 metric=VectorMetric.COSINE,
             )
             print(f"[CandidateStore] Created AstraDB collection: {CANDIDATE_COLLECTION}")

        return _collection
    except Exception as e:
        print(f"[CandidateStore] AstraDB connection failed: {e}")
        return None


def _generate_embedding(text: str):
    """Generate embedding vector for a text chunk."""
    from sentence_transformers import SentenceTransformer

    # Reuse the existing model loader
    try:
        from resume_processor_rag.core.embeddings_generator import generate_embeddings
        return generate_embeddings(text)
    except ImportError:
        # Fallback: load directly
        model = SentenceTransformer("all-mpnet-base-v2")
        return model.encode(text)


# ── Public API ────────────────────────────────────────────────────────────────

def ingest_candidate(candidate: CandidateInput) -> Dict:
    """Process candidate data into chunks, embed, and store in AstraDB.

    Returns dict with candidate_id and chunks_stored count.
    """
    chunks = _build_chunks(candidate)
    collection = _get_collection()

    if collection is None:
        # Memory-only mode — just return the chunks as context
        return {
            "candidate_id": candidate.candidate_id,
            "chunks_stored": 0,
            "context_text": "\n\n".join(c["content"] for c in chunks),
        }

    records = []
    for chunk in chunks:
        embedding = _generate_embedding(chunk["content"])
        records.append({
            "candidate_id": candidate.candidate_id,
            "job_id": candidate.job_id,
            "chunk_type": chunk["type"],
            "content": chunk["content"],
            "$vector": embedding.tolist(),
            "created_at": datetime.utcnow().isoformat(),
        })

    if records:
        collection.insert_many(records)

    return {
        "candidate_id": candidate.candidate_id,
        "chunks_stored": len(records),
        "context_text": "\n\n".join(c["content"] for c in chunks),
    }


def get_candidate_context(candidate_id: str, query: str = "", limit: int = 10) -> str:
    """Retrieve relevant candidate context from AstraDB via vector search."""
    collection = _get_collection()
    if collection is None:
        return ""

    search_query = query or "professional skills experience projects education"
    embedding = _generate_embedding(search_query)

    results = collection.find(
        filter={"candidate_id": candidate_id},
        sort={"$vector": embedding.tolist()},
        limit=limit,
    )

    chunks = [doc.get("content", "") for doc in results]
    return "\n\n".join(chunks)


# ── Chunk Builder ─────────────────────────────────────────────────────────────

def _build_chunks(candidate: CandidateInput) -> List[Dict]:
    """Break candidate input into embeddable text chunks."""
    chunks = []

    # Job description chunk
    if candidate.job_description:
        chunks.append({
            "type": "JOB_DESCRIPTION",
            "content": f"Job Description:\n{candidate.job_description}",
        })

    # Skills chunk
    if candidate.skills:
        chunks.append({
            "type": "SKILLS",
            "content": f"Technical Skills: {', '.join(candidate.skills)}",
        })

    # Education chunk
    if candidate.education:
        chunks.append({
            "type": "EDUCATION",
            "content": f"Education: {candidate.education}",
        })

    # Each project as its own chunk
    for i, project in enumerate(candidate.projects):
        text = f"Project {i+1}:\n{project.description}"
        if project.skills:
            text += f"\nTechnologies: {project.skills}"
        chunks.append({"type": "PROJECT", "content": text})

    # LeetCode profile
    if candidate.leetcode_profile:
        chunks.append({
            "type": "LEETCODE",
            "content": f"LeetCode Profile: {candidate.leetcode_profile}",
        })

    return chunks
