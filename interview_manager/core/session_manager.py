"""Session lifecycle management — create, retrieve, end sessions."""

import time
from typing import Dict, Optional

from interview_manager.models.interview_models import InterviewSession, InterviewSummary
from interview_manager.core.interview_state import InterviewState


class SessionManager:
    """Manages active interview sessions."""

    def __init__(self):
        self._sessions: Dict[str, InterviewState] = {}

    def create_session(self, user_id: str, resume_context: str = "") -> InterviewState:
        """Create a new interview session and return its state."""
        session = InterviewSession(
            user_id=user_id,
            resume_context=resume_context,
        )
        state = InterviewState(session)
        self._sessions[session.session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[InterviewState]:
        """Retrieve an active session by ID."""
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> Optional[InterviewSummary]:
        """End a session and return a summary."""
        state = self._sessions.get(session_id)
        if not state:
            return None

        state.session.is_active = False
        state.session.ended_at = time.time()

        summary = InterviewSummary(
            session_id=session_id,
            duration_mins=round(state.session.elapsed_mins, 1),
            total_questions=state.session.total_questions,
            phases_completed=list(state.session.questions_asked.keys()),
            transcript_length=len(state.session.transcript),
            violation_count=state.violation_count,
            avg_attention_score=round(state.avg_attention, 3),
            transcript=[e.model_dump() for e in state.session.transcript],
            qa_history=[qa.model_dump() for qa in state.session.qa_history],
        )

        return summary

    def remove_session(self, session_id: str):
        """Remove a session from memory."""
        self._sessions.pop(session_id, None)

    @property
    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.session.is_active)

    def list_sessions(self) -> list:
        return [
            {"session_id": sid, "active": s.session.is_active, "phase": s.current_phase.value}
            for sid, s in self._sessions.items()
        ]
