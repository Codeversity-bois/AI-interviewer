"""Pydantic models for the live interview microservice."""

import time
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ── Input Schema ──────────────────────────────────────────────────────────────

class ProjectInfo(BaseModel):
    description: str = ""
    skills: str = ""


class CandidateInput(BaseModel):
    """Input payload to start a live interview session."""
    candidate_id: str
    job_id: str
    job_description: str
    projects: List[ProjectInfo] = []
    skills: List[str] = []
    education: str = ""
    leetcode_profile: str = ""


# ── Evaluation Models ─────────────────────────────────────────────────────────

class TurnEvaluation(BaseModel):
    """Evaluation of a single candidate turn."""
    turn_number: int
    question_asked: str
    candidate_response: str
    relevance_score: float = 0.0          # 0-10
    depth_score: float = 0.0              # 0-10
    communication_score: float = 0.0      # 0-10
    technical_accuracy: float = 0.0       # 0-10
    key_observations: List[str] = []
    red_flags: List[str] = []
    follow_up_needed: bool = False
    follow_up_reason: str = ""


class InterviewEvaluation(BaseModel):
    """Running evaluation of the entire interview, updated after each turn."""
    candidate_id: str
    job_id: str
    session_id: str
    turns: List[TurnEvaluation] = []
    overall_score: float = 0.0            # 0-10 running average
    technical_competency: float = 0.0     # 0-10
    communication_skills: float = 0.0     # 0-10
    problem_solving: float = 0.0          # 0-10
    cultural_fit: float = 0.0             # 0-10
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendation: str = ""              # "strong_hire" / "hire" / "lean_no" / "no_hire"
    updated_at: float = Field(default_factory=time.time)


# ── Transcript ────────────────────────────────────────────────────────────────

class TranscriptTurn(BaseModel):
    role: str               # "interviewer" or "candidate"
    text: str
    timestamp: float = Field(default_factory=time.time)


class InterviewSession(BaseModel):
    """Full session state for a live interview."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str = ""
    job_id: str = ""
    transcript: List[TranscriptTurn] = []
    evaluation: Optional[InterviewEvaluation] = None
    proctoring_report: Optional[Dict[str, Any]] = None  # Proctoring violations and metrics
    started_at: float = Field(default_factory=time.time)
    ended_at: Optional[float] = None
    is_active: bool = True

    @property
    def turn_count(self) -> int:
        return len([t for t in self.transcript if t.role == "candidate"])

    @property
    def elapsed_mins(self) -> float:
        return (time.time() - self.started_at) / 60.0
