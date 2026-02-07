"""Data models for interview sessions."""

import time
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from interview_manager.config import InterviewPhase


class TranscriptEntry(BaseModel):
    role: str               # "ai" or "user"
    text: str
    timestamp: float = Field(default_factory=time.time)
    phase: Optional[InterviewPhase] = None
    feedback: Optional[str] = None
    verification_data: Optional[Dict[str, Any]] = None


class QAPair(BaseModel):
    question: str
    answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None  # VerificationReport dump
    timestamp: float = Field(default_factory=time.time)

class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    resume_context: str = ""
    current_phase: InterviewPhase = InterviewPhase.INTRO
    questions_asked: Dict[str, int] = Field(default_factory=dict)  # phase → count
    transcript: List[TranscriptEntry] = []
    qa_history: List[QAPair] = []  # Structured Q&A history
    started_at: float = Field(default_factory=time.time)
    ended_at: Optional[float] = None
    is_active: bool = True

    @property
    def total_questions(self) -> int:
        return sum(self.questions_asked.values())

    @property
    def elapsed_mins(self) -> float:
        return (time.time() - self.started_at) / 60.0

    def add_entry(self, role: str, text: str) -> int:
        entry = TranscriptEntry(
            role=role, text=text, phase=self.current_phase,
        )
        self.transcript.append(entry)
        return len(self.transcript) - 1

    def update_entry(self, index: int, feedback: str = None, verification_data: Dict = None):
        if 0 <= index < len(self.transcript):
            entry = self.transcript[index]
            if feedback:
                entry.feedback = feedback
            if verification_data:
                entry.verification_data = verification_data

    def increment_question(self):
        phase_key = self.current_phase.value
        self.questions_asked[phase_key] = self.questions_asked.get(phase_key, 0) + 1


class InterviewStatus(BaseModel):
    session_id: str
    is_active: bool
    current_phase: str
    total_questions: int
    elapsed_mins: float
    attention_score: Optional[float] = None
    violation_count: int = 0


class InterviewSummary(BaseModel):
    session_id: str
    duration_mins: float
    total_questions: int
    phases_completed: List[str]
    transcript_length: int
    violation_count: int
    avg_attention_score: float
    transcript: List[Dict[str, Any]] = []
    qa_history: List[Dict[str, Any]] = []
