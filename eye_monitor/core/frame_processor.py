"""Orchestrates the per-frame proctoring pipeline."""

import time
from typing import Optional

import numpy as np

from eye_monitor.core.face_detector import FaceDetector
from eye_monitor.core.gaze_tracker import GazeTracker
from eye_monitor.core.attention_scorer import AttentionScorer
from eye_monitor.core.violation_detector import ViolationDetector
from eye_monitor.models.proctoring_events import FrameAnalysis, ProctoringReport


class FrameProcessor:
    """Takes a raw frame, runs the full detection pipeline, returns analysis."""

    def __init__(self):
        self.face_detector = FaceDetector()
        self.gaze_tracker = GazeTracker()
        self.attention_scorer = AttentionScorer()
        self.violation_detector = ViolationDetector()
        self._total_frames = 0
        self._face_present_count = 0

    def process(self, frame: np.ndarray, timestamp: Optional[float] = None) -> FrameAnalysis:
        """Full pipeline: detect face → track gaze → score attention → check violations."""
        ts = timestamp or time.time()
        self._total_frames += 1

        # Step 1: Face detection
        face = self.face_detector.detect(frame)

        gaze = None
        attention = None

        if face.face_present and face.landmarks:
            self._face_present_count += 1

            # Step 2: Gaze tracking (needs landmarks)
            gaze = self.gaze_tracker.estimate_gaze(face.landmarks)

            # Step 3: Attention scoring
            attention = self.attention_scorer.update(gaze, ts)

        # Step 4: Violation detection
        violations = self.violation_detector.evaluate(face, gaze, attention, ts)

        return FrameAnalysis(
            face=face,
            gaze=gaze,
            attention=attention,
            violations=violations,
            timestamp=ts,
        )

    def get_report(self) -> ProctoringReport:
        """Generate a summary report of the entire session."""
        all_violations = self.violation_detector.get_all_violations()
        attention = self.attention_scorer.get_score()

        face_pct = 0.0
        if self._total_frames > 0:
            face_pct = (self._face_present_count / self._total_frames) * 100.0

        return ProctoringReport(
            total_frames=self._total_frames,
            total_violations=len(all_violations),
            violations=all_violations,
            avg_attention_score=attention.score,
            screen_focus_pct=attention.screen_focus_pct,
            face_present_pct=round(face_pct, 1),
        )

    def reset(self):
        self.attention_scorer.reset()
        self.violation_detector.reset()
        self._total_frames = 0
        self._face_present_count = 0

    def close(self):
        self.face_detector.close()
