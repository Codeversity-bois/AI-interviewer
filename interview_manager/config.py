"""Interview manager configuration."""

from enum import Enum


class InterviewPhase(str, Enum):
    INTRO = "intro"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    PROJECT_DEEP_DIVE = "project_deep_dive"
    WRAP_UP = "wrap_up"


class InterviewConfig:
    # Phase question limits
    PHASE_QUESTIONS = {
        InterviewPhase.INTRO: 2,
        InterviewPhase.BEHAVIORAL: 3,
        InterviewPhase.TECHNICAL: 4,
        InterviewPhase.PROJECT_DEEP_DIVE: 4,
        InterviewPhase.WRAP_UP: 2,
    }

    # Phase order
    PHASE_ORDER = [
        InterviewPhase.INTRO,
        InterviewPhase.BEHAVIORAL,
        InterviewPhase.TECHNICAL,
        InterviewPhase.PROJECT_DEEP_DIVE,
        InterviewPhase.WRAP_UP,
    ]

    # Timing
    MAX_INTERVIEW_DURATION_MINS = 30
    SESSION_TIMEOUT_MINS = 45

    # Gemini
    GEMINI_MODEL = "gemini-2.5-flash"
    TEMPERATURE = 0.7
    MAX_OUTPUT_TOKENS = 2048
