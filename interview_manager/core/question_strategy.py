"""Decides what question to ask next — follow-up from verifier or phase progression."""

from typing import Optional

from interview_manager.config import InterviewPhase, InterviewConfig
from interview_manager.core.interview_state import InterviewState
from answer_verifier.models.verification_models import FollowupQuestion, FollowupPriority


class QuestionStrategy:
    """Picks the next question: high-priority follow-up > phase question > low-priority follow-up."""

    def should_transition_phase(self, state: InterviewState) -> bool:
        """Check if we should move to the next phase."""
        phase = state.current_phase
        max_q = InterviewConfig.PHASE_QUESTIONS.get(phase, 3)
        asked = state.questions_in_phase()

        # Time limit check
        if state.session.elapsed_mins >= InterviewConfig.MAX_INTERVIEW_DURATION_MINS:
            return True

        return asked >= max_q

    def next_phase(self, current: InterviewPhase) -> Optional[InterviewPhase]:
        """Get the next phase in sequence. Returns None if interview is over."""
        order = InterviewConfig.PHASE_ORDER
        try:
            idx = order.index(current)
            if idx + 1 < len(order):
                return order[idx + 1]
        except ValueError:
            pass
        return None

    def pick_next_action(
        self,
        state: InterviewState,
        followup: Optional[FollowupQuestion] = None,
    ) -> dict:
        """Decide what to do next.

        Returns:
            {"action": "ask_followup", "question": FollowupQuestion}
            {"action": "ask_phase_question", "phase": InterviewPhase}
            {"action": "transition_phase", "new_phase": InterviewPhase}
            {"action": "end_interview"}
        """
        # High priority follow-up always takes precedence
        if followup and followup.priority == FollowupPriority.HIGH:
            return {"action": "ask_followup", "question": followup}

        # Check if we need to change phase
        if self.should_transition_phase(state):
            new_phase = self.next_phase(state.current_phase)
            if new_phase is None:
                return {"action": "end_interview"}
            return {"action": "transition_phase", "new_phase": new_phase}

        # Medium priority follow-up if we still have room in phase
        if followup and followup.priority == FollowupPriority.MEDIUM:
            return {"action": "ask_followup", "question": followup}

        # Default: ask a normal phase question
        return {"action": "ask_phase_question", "phase": state.current_phase}
