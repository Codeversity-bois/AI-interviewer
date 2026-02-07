"""Centralized interview state tracking."""

import time
from typing import List, Optional, Dict

from interview_manager.config import InterviewPhase
from interview_manager.models.interview_models import InterviewSession, TranscriptEntry, QAPair
from eye_monitor.models.proctoring_events import Violation, AttentionScore
from answer_verifier.models.verification_models import FollowupQuestion


class InterviewState:
    """Single source of truth for everything happening in an interview."""

    def __init__(self, session: InterviewSession):
        self.session = session
        self.violations: List[Violation] = []
        self.attention_scores: List[float] = []
        self._last_question: str = ""
        self._is_technical_question: bool = False
        self._current_qa: Optional[QAPair] = None
        self._pending_answer_buffer: List[str] = []

    # --- transcript ---

    def add_ai_message(self, text: str):
        self.session.add_entry("ai", text)
        self._last_question = text

    def add_user_message(self, text: str) -> int:
        return self.session.add_entry("user", text)

    def update_transcript_entry(self, index: int, feedback: str = None, verification_data: Dict = None):
        self.session.update_entry(index, feedback, verification_data)

    @property
    def last_user_message(self) -> str:
        for entry in reversed(self.session.transcript):
            if entry.role == "user":
                return entry.text
        return ""

    @property
    def last_question(self) -> str:
        return self._last_question

    # --- Q&A Lifecycle ---

    def start_new_qa(self, question: str):
        """Called when AI asks a new question."""
        if self._current_qa and not self._current_qa.answer:
             # Previous question wasn't answered? Close it as unanswered.
             self._current_qa.answer = "(No answer provided)"
             self.session.qa_history.append(self._current_qa)
        
        self._current_qa = QAPair(question=question)
        self._pending_answer_buffer = []

    def buffer_user_input(self, text: str):
        """Accumulate user speech chunks."""
        self._pending_answer_buffer.append(text)

    def finalize_answer(self, evaluation: Dict = None) -> QAPair:
        """Mark the current answer as complete and store in history."""
        if not self._current_qa:
            return None
            
        full_answer = " ".join(self._pending_answer_buffer)
        self._current_qa.answer = full_answer
        self._current_qa.evaluation = evaluation
        
        self.session.qa_history.append(self._current_qa)
        completed_qa = self._current_qa
        
        # Reset for next turn
        self._current_qa = None
        self._pending_answer_buffer = []
        
        return completed_qa

    @property
    def current_qa(self) -> Optional[QAPair]:
        return self._current_qa

    # --- phase management ---

    @property
    def current_phase(self) -> InterviewPhase:
        return self.session.current_phase

    def set_phase(self, phase: InterviewPhase):
        self.session.current_phase = phase

    def questions_in_phase(self) -> int:
        return self.session.questions_asked.get(self.session.current_phase.value, 0)

    def record_question_asked(self):
        self.session.increment_question()

    # --- proctoring ---

    def add_violation(self, violation: Violation):
        self.violations.append(violation)

    def update_attention(self, score: float):
        self.attention_scores.append(score)

    @property
    def avg_attention(self) -> float:
        if not self.attention_scores:
            return 1.0
        return sum(self.attention_scores) / len(self.attention_scores)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    # --- question context ---

    @property
    def is_technical_question(self) -> bool:
        return self._is_technical_question

    def set_technical_question(self, val: bool):
        self._is_technical_question = val

    # --- serialization ---

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session.session_id,
            "phase": self.session.current_phase.value,
            "total_questions": self.session.total_questions,
            "elapsed_mins": round(self.session.elapsed_mins, 1),
            "violation_count": self.violation_count,
            "avg_attention": round(self.avg_attention, 3),
            "is_active": self.session.is_active,
        }
