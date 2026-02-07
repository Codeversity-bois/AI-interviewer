"""Conversation intelligence configuration."""


class ConversationConfig:
    # Silence thresholds (milliseconds)
    THINKING_PAUSE_MS = 2000          # < this = still thinking
    DONE_SPEAKING_MS = 5000           # > this = probably done
    STUCK_SILENCE_MS = 15000          # > this = stuck, offer help

    # Audio energy
    SILENCE_RMS_THRESHOLD = 500       # below this RMS = silence
    SPEECH_RMS_THRESHOLD = 1000       # above this = speech

    # Backchannel
    BACKCHANNEL_COOLDOWN_MS = 10000   # min gap between "hmm" / "go on"
    BACKCHANNEL_AFTER_MS = 4000       # inject backchannel after this silence

    # Interrupts
    INTERRUPT_GRACE_PERIOD_MS = 500   # wait this long before confirming interrupt

    # Question complexity → extra patience
    TECHNICAL_EXTRA_PATIENCE_MS = 3000
