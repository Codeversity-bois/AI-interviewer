"""State machine for tracking who's speaking and conversation flow."""

import time

from conversation_intelligence.config import ConversationConfig
from conversation_intelligence.models.conversation_states import SpeechState, SpeechEvent


class SpeechStateMachine:
    """Tracks the current state of the conversation turn."""

    def __init__(self):
        self.state = SpeechState.IDLE
        self._state_entered_at = time.time()

    def transition(self, event: SpeechEvent) -> SpeechState:
        """Process an event and return the new state."""
        prev = self.state

        if event == SpeechEvent.AI_RESPONSE_STARTED:
            self.state = SpeechState.AI_SPEAKING

        elif event == SpeechEvent.AI_RESPONSE_ENDED:
            self.state = SpeechState.IDLE

        elif event == SpeechEvent.SPEECH_STARTED:
            self.state = SpeechState.USER_SPEAKING

        elif event == SpeechEvent.SPEECH_ENDED:
            self.state = SpeechState.USER_THINKING

        elif event == SpeechEvent.SILENCE_MEDIUM:
            if self.state == SpeechState.USER_THINKING:
                # still thinking — stay
                pass

        elif event == SpeechEvent.SILENCE_LONG:
            if self.state in (SpeechState.USER_THINKING, SpeechState.USER_SPEAKING):
                self.state = SpeechState.USER_FINISHED

        elif event == SpeechEvent.USER_INTERRUPT:
            self.state = SpeechState.USER_SPEAKING

        if self.state != prev:
            self._state_entered_at = time.time()

        return self.state

    @property
    def time_in_state_ms(self) -> float:
        return (time.time() - self._state_entered_at) * 1000

    @property
    def current(self) -> SpeechState:
        return self.state
