"""Handles user interrupts during AI speech."""

import time
from typing import Optional

from conversation_intelligence.config import ConversationConfig
from conversation_intelligence.models.conversation_states import SpeechState


class InterruptController:
    """Detects when the user wants to interrupt and handles it gracefully."""

    def __init__(self):
        self._interrupt_detected_at: Optional[float] = None

    def should_interrupt(self, state: SpeechState, user_is_speaking: bool) -> bool:
        """Returns True if AI should stop talking because user started speaking."""
        if state != SpeechState.AI_SPEAKING:
            self._interrupt_detected_at = None
            return False

        if not user_is_speaking:
            self._interrupt_detected_at = None
            return False

        now = time.time()

        # First detection — start grace period
        if self._interrupt_detected_at is None:
            self._interrupt_detected_at = now
            return False

        # Check if grace period has passed (user is consistently speaking)
        elapsed_ms = (now - self._interrupt_detected_at) * 1000
        if elapsed_ms >= ConversationConfig.INTERRUPT_GRACE_PERIOD_MS:
            self._interrupt_detected_at = None
            return True

        return False

    def get_acknowledgment(self) -> str:
        """What the AI says when it yields the floor."""
        responses = [
            "Sure, go ahead.",
            "Of course, please continue.",
            "Yes, go on.",
        ]
        # Rotate through responses
        idx = int(time.time()) % len(responses)
        return responses[idx]
