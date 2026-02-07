"""Inject natural backchannel responses during user thinking pauses."""

import time
from typing import Optional

from conversation_intelligence.config import ConversationConfig
from conversation_intelligence.models.conversation_states import SpeechState


# Phrases grouped by context
THINKING_PHRASES = [
    "Take your time.",
    "No rush.",
    "Sure, think about it.",
]

ENCOURAGEMENT_PHRASES = [
    "Hmm, interesting.",
    "I see.",
    "Right.",
    "Go on.",
]

STUCK_PHRASES = [
    "Would you like me to rephrase the question?",
    "Would you like to move on to the next question?",
    "Do you want me to give you a hint?",
]


class BackchannelEngine:
    """Generates natural filler responses to make the conversation feel human."""

    def __init__(self):
        self._last_backchannel_time: float = 0.0
        self._phrase_index: int = 0

    def get_response(
        self, state: SpeechState, silence_duration_ms: float
    ) -> Optional[str]:
        """Returns a backchannel phrase if appropriate, else None."""
        now = time.time()
        cooldown_elapsed = (now - self._last_backchannel_time) * 1000

        if cooldown_elapsed < ConversationConfig.BACKCHANNEL_COOLDOWN_MS:
            return None

        if state != SpeechState.USER_THINKING:
            return None

        phrase = None

        # User stuck for a very long time
        if silence_duration_ms >= ConversationConfig.STUCK_SILENCE_MS:
            phrase = self._pick(STUCK_PHRASES)

        # Normal thinking pause — gentle encouragement
        elif silence_duration_ms >= ConversationConfig.BACKCHANNEL_AFTER_MS:
            phrase = self._pick(THINKING_PHRASES)

        if phrase:
            self._last_backchannel_time = now

        return phrase

    def _pick(self, phrases: list) -> str:
        idx = self._phrase_index % len(phrases)
        self._phrase_index += 1
        return phrases[idx]
