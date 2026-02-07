"""Ring buffer for incoming video frames."""

from collections import deque
from typing import Optional

import numpy as np

from eye_monitor.config import EyeMonitorConfig


class FrameBuffer:
    """Thread-safe-ish ring buffer for video frames."""

    def __init__(self, max_size: int = EyeMonitorConfig.FRAME_BUFFER_SIZE):
        self._buffer: deque = deque(maxlen=max_size)

    def push(self, frame: np.ndarray, timestamp: float):
        self._buffer.append((frame, timestamp))

    def pop(self) -> Optional[tuple]:
        """Get oldest frame. Returns (frame, timestamp) or None."""
        if self._buffer:
            return self._buffer.popleft()
        return None

    def latest(self) -> Optional[tuple]:
        """Peek at the newest frame without removing it."""
        if self._buffer:
            return self._buffer[-1]
        return None

    @property
    def size(self) -> int:
        return len(self._buffer)

    def clear(self):
        self._buffer.clear()
