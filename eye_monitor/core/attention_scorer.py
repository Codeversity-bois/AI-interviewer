"""Rolling attention score from gaze samples."""

import time
from collections import deque
from typing import Optional

from eye_monitor.config import EyeMonitorConfig
from eye_monitor.models.proctoring_events import AttentionScore, GazeResult


class AttentionScorer:
    """Maintains a sliding window of gaze samples and computes attention score."""

    def __init__(self):
        self._samples: deque = deque()  # (timestamp, is_looking_at_screen)

    def update(self, gaze: GazeResult, timestamp: Optional[float] = None) -> AttentionScore:
        """Add a gaze sample and return the current rolling score."""
        ts = timestamp or time.time()
        self._samples.append((ts, gaze.is_looking_at_screen))
        self._prune(ts)
        return self._compute()

    def get_score(self) -> AttentionScore:
        """Get current score without adding a sample."""
        self._prune(time.time())
        return self._compute()

    def reset(self):
        self._samples.clear()

    def _prune(self, now: float):
        """Remove samples older than the sliding window."""
        cutoff = now - EyeMonitorConfig.SLIDING_WINDOW_SECS
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _compute(self) -> AttentionScore:
        n = len(self._samples)
        if n == 0:
            return AttentionScore(score=1.0, screen_focus_pct=100.0, sample_count=0)

        looking = sum(1 for _, on_screen in self._samples if on_screen)
        pct = (looking / n) * 100.0
        score = looking / n  # simple ratio

        return AttentionScore(
            score=round(score, 3),
            screen_focus_pct=round(pct, 1),
            sample_count=n,
        )
