"""Detect silence in audio chunks and classify pause duration."""

import struct
import math
import time
from typing import Optional

from conversation_intelligence.config import ConversationConfig
from conversation_intelligence.models.conversation_states import SilenceAnalysis, SpeechEvent


class SilenceDetector:
    """Analyzes audio chunks to detect silence vs speech."""

    def __init__(self):
        self._silence_start: Optional[float] = None
        self._is_silent = False

    def analyze(self, audio_chunk: bytes, sample_rate: int = 16000) -> SilenceAnalysis:
        """Compute RMS energy of a PCM16 audio chunk and determine silence state."""
        rms = self._compute_rms(audio_chunk)
        now = time.time()

        is_silent = rms < ConversationConfig.SILENCE_RMS_THRESHOLD

        if is_silent and not self._is_silent:
            # transition to silence
            self._silence_start = now
            self._is_silent = True
        elif not is_silent:
            self._is_silent = False
            self._silence_start = None

        duration_ms = 0.0
        if self._is_silent and self._silence_start:
            duration_ms = (now - self._silence_start) * 1000

        return SilenceAnalysis(
            is_silent=is_silent,
            duration_ms=round(duration_ms, 0),
            rms_energy=round(rms, 1),
        )

    def classify_silence(self, analysis: SilenceAnalysis) -> Optional[SpeechEvent]:
        """Convert silence duration into a speech event."""
        if not analysis.is_silent:
            if analysis.rms_energy >= ConversationConfig.SPEECH_RMS_THRESHOLD:
                return SpeechEvent.SPEECH_STARTED
            return None

        if analysis.duration_ms >= ConversationConfig.DONE_SPEAKING_MS:
            return SpeechEvent.SILENCE_LONG
        elif analysis.duration_ms >= ConversationConfig.THINKING_PAUSE_MS:
            return SpeechEvent.SILENCE_MEDIUM
        elif analysis.duration_ms > 0:
            return SpeechEvent.SILENCE_SHORT

        return None

    @staticmethod
    def _compute_rms(audio_chunk: bytes) -> float:
        """Compute Root Mean Square energy from PCM16 little-endian audio."""
        if len(audio_chunk) < 2:
            return 0.0
        n_samples = len(audio_chunk) // 2
        samples = struct.unpack(f"<{n_samples}h", audio_chunk[:n_samples * 2])
        if not samples:
            return 0.0
        sum_sq = sum(s * s for s in samples)
        return math.sqrt(sum_sq / n_samples)
