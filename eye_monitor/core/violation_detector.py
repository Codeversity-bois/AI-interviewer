"""Detect proctoring violations from face/gaze/attention data."""

import time
from typing import List, Optional

from eye_monitor.config import EyeMonitorConfig
from eye_monitor.models.proctoring_events import (
    FaceDetectionResult,
    GazeResult,
    AttentionScore,
    Violation,
    ViolationType,
    Severity,
)


class ViolationDetector:
    """Tracks ongoing violation state and emits violations when thresholds are crossed."""

    def __init__(self):
        self._no_face_start: Optional[float] = None
        self._multi_face_start: Optional[float] = None
        self._gaze_off_start: Optional[float] = None
        self._violations: List[Violation] = []

    def evaluate(
        self,
        face: FaceDetectionResult,
        gaze: Optional[GazeResult],
        attention: Optional[AttentionScore],
        timestamp: Optional[float] = None,
    ) -> List[Violation]:
        """Check all rules and return any new violations."""
        now = timestamp or time.time()
        new_violations: List[Violation] = []

        # Rule 1: No face detected
        new_violations.extend(self._check_no_face(face, now))

        # Rule 2: Multiple faces
        new_violations.extend(self._check_multiple_faces(face, now))

        # Rule 3: Gaze off screen
        if gaze:
            new_violations.extend(self._check_gaze_off(gaze, now))

        # Rule 4: Low attention
        if attention:
            new_violations.extend(self._check_low_attention(attention, now))

        self._violations.extend(new_violations)
        return new_violations

    def get_all_violations(self) -> List[Violation]:
        return list(self._violations)

    def reset(self):
        self._no_face_start = None
        self._multi_face_start = None
        self._gaze_off_start = None
        self._violations.clear()

    # --- rule checks ---

    def _check_no_face(self, face: FaceDetectionResult, now: float) -> List[Violation]:
        if not face.face_present:
            if self._no_face_start is None:
                self._no_face_start = now
            duration = now - self._no_face_start
            if duration >= EyeMonitorConfig.FACE_ABSENCE_LIMIT_SECS:
                self._no_face_start = now  # reset to avoid spamming
                return [Violation(
                    type=ViolationType.NO_FACE,
                    severity=self._severity_by_duration(duration),
                    duration_secs=round(duration, 1),
                    message=f"No face detected for {duration:.1f}s",
                    timestamp=now,
                )]
        else:
            self._no_face_start = None
        return []

    def _check_multiple_faces(self, face: FaceDetectionResult, now: float) -> List[Violation]:
        if face.face_count > 1:
            if self._multi_face_start is None:
                self._multi_face_start = now
            duration = now - self._multi_face_start
            if duration >= EyeMonitorConfig.MULTIPLE_FACES_LIMIT_SECS:
                self._multi_face_start = now
                return [Violation(
                    type=ViolationType.MULTIPLE_FACES,
                    severity=Severity.HIGH,
                    duration_secs=round(duration, 1),
                    message=f"Multiple faces detected ({face.face_count}) for {duration:.1f}s",
                    timestamp=now,
                )]
        else:
            self._multi_face_start = None
        return []

    def _check_gaze_off(self, gaze: GazeResult, now: float) -> List[Violation]:
        if not gaze.is_looking_at_screen:
            if self._gaze_off_start is None:
                self._gaze_off_start = now
            duration = now - self._gaze_off_start
            if duration >= EyeMonitorConfig.GAZE_OFF_SCREEN_LIMIT_SECS:
                self._gaze_off_start = now
                return [Violation(
                    type=ViolationType.GAZE_OFF_SCREEN,
                    severity=self._severity_by_duration(duration),
                    duration_secs=round(duration, 1),
                    message=f"Looking {gaze.direction.value} for {duration:.1f}s",
                    timestamp=now,
                )]
        else:
            self._gaze_off_start = None
        return []

    def _check_low_attention(self, attention: AttentionScore, now: float) -> List[Violation]:
        if attention.score < EyeMonitorConfig.MIN_ATTENTION_SCORE and attention.sample_count > 5:
            return [Violation(
                type=ViolationType.LOW_ATTENTION,
                severity=Severity.MEDIUM,
                duration_secs=EyeMonitorConfig.SLIDING_WINDOW_SECS,
                message=f"Attention score {attention.score:.2f} below threshold",
                timestamp=now,
            )]
        return []

    @staticmethod
    def _severity_by_duration(duration: float) -> Severity:
        if duration > 15:
            return Severity.CRITICAL
        if duration > 10:
            return Severity.HIGH
        if duration > 5:
            return Severity.MEDIUM
        return Severity.LOW
