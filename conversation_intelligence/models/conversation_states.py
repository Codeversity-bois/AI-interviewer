"""Enums and models for conversation state management."""

from enum import Enum
from pydantic import BaseModel


class SpeechState(str, Enum):
    AI_SPEAKING = "ai_speaking"
    USER_SPEAKING = "user_speaking"
    USER_THINKING = "user_thinking"
    USER_FINISHED = "user_finished"
    IDLE = "idle"


class SpeechEvent(str, Enum):
    SPEECH_STARTED = "speech_started"
    SPEECH_ENDED = "speech_ended"
    SILENCE_SHORT = "silence_short"       # < 2s
    SILENCE_MEDIUM = "silence_medium"     # 2-5s
    SILENCE_LONG = "silence_long"         # > 5s
    AI_RESPONSE_STARTED = "ai_response_started"
    AI_RESPONSE_ENDED = "ai_response_ended"
    USER_INTERRUPT = "user_interrupt"


class SilenceAnalysis(BaseModel):
    is_silent: bool
    duration_ms: float
    rms_energy: float


class TurnDecision(BaseModel):
    should_speak: bool
    wait_ms: int = 0
    reason: str = ""
    backchannel: str = ""  # e.g. "Take your time" — empty means no backchannel
