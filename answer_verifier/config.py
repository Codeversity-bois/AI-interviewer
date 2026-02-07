"""Answer verifier configuration."""


class VerifierConfig:
    MAX_CLAIMS_PER_RESPONSE = 5
    VERIFICATION_TIMEOUT_SECS = 10
    MIN_CONFIDENCE_TO_PROBE = 0.4       # below this = definitely probe
    FOLLOWUP_QUEUE_MAX = 10
    GEMINI_MODEL = "gemini-2.5-flash"
    VERIFICATION_TEMPERATURE = 0.3      # low temp for factual analysis
