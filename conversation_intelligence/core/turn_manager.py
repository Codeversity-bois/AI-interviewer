"""Decides when the AI should speak, wait, or backchannel."""

from conversation_intelligence.config import ConversationConfig
from conversation_intelligence.models.conversation_states import (
    SpeechState,
    SilenceAnalysis,
    TurnDecision,
)


class TurnManager:
    """Makes turn-taking decisions based on conversation state and silence."""

    def should_ai_speak(
        self,
        state: SpeechState,
        silence: SilenceAnalysis,
        is_technical_question: bool = False,
    ) -> TurnDecision:
        """Decide if the AI should respond, wait, or inject a backchannel."""

        # User is actively talking — never interrupt
        if state == SpeechState.USER_SPEAKING:
            return TurnDecision(should_speak=False, reason="user is speaking")

        # AI is already talking
        if state == SpeechState.AI_SPEAKING:
            return TurnDecision(should_speak=False, reason="ai is already speaking")

        # User is thinking
        if state == SpeechState.USER_THINKING:
            patience = ConversationConfig.DONE_SPEAKING_MS
            if is_technical_question:
                patience += ConversationConfig.TECHNICAL_EXTRA_PATIENCE_MS

            if silence.duration_ms < patience:
                return TurnDecision(
                    should_speak=False,
                    wait_ms=int(patience - silence.duration_ms),
                    reason="user is thinking, waiting",
                )

            # Patience exceeded — user is probably done
            return TurnDecision(should_speak=True, reason="silence exceeded patience")

        # User finished speaking
        if state == SpeechState.USER_FINISHED:
            return TurnDecision(should_speak=True, reason="user finished speaking")

        # Idle — AI can go ahead
        if state == SpeechState.IDLE:
            return TurnDecision(should_speak=True, reason="idle, ready for next question")

        return TurnDecision(should_speak=False, reason="unknown state")
