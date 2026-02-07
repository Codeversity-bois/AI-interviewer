"""Gaze direction estimation from face mesh landmarks."""

import math
from typing import List, Tuple

from eye_monitor.config import EyeMonitorConfig
from eye_monitor.models.proctoring_events import GazeResult, GazeDirection

# MediaPipe FaceMesh landmark indices
# Left eye outline
LEFT_EYE = [362, 385, 387, 263, 373, 380]
# Right eye outline
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
# Iris centers (refined landmarks)
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


class GazeTracker:
    """Estimates where the user is looking from iris + eye landmarks."""

    def estimate_gaze(self, landmarks: List[Tuple[float, float, float]]) -> GazeResult:
        """Compute gaze direction from 478 face mesh landmarks."""
        h_ratio_left = self._iris_horizontal_ratio(landmarks, LEFT_EYE, LEFT_IRIS)
        h_ratio_right = self._iris_horizontal_ratio(landmarks, RIGHT_EYE, RIGHT_IRIS)
        h_ratio = (h_ratio_left + h_ratio_right) / 2.0

        v_ratio_left = self._iris_vertical_ratio(landmarks, LEFT_EYE, LEFT_IRIS)
        v_ratio_right = self._iris_vertical_ratio(landmarks, RIGHT_EYE, RIGHT_IRIS)
        v_ratio = (v_ratio_left + v_ratio_right) / 2.0

        ear_left = self._eye_aspect_ratio(landmarks, LEFT_EYE)
        ear_right = self._eye_aspect_ratio(landmarks, RIGHT_EYE)

        direction = self._classify_direction(h_ratio, v_ratio)
        threshold = EyeMonitorConfig.GAZE_CENTER_THRESHOLD
        is_center = (
            abs(h_ratio - 0.5) < threshold and abs(v_ratio - 0.5) < threshold
        )

        return GazeResult(
            direction=direction,
            horizontal_ratio=round(h_ratio, 3),
            vertical_ratio=round(v_ratio, 3),
            is_looking_at_screen=is_center,
            ear_left=round(ear_left, 3),
            ear_right=round(ear_right, 3),
        )

    # --- private helpers ---

    def _iris_horizontal_ratio(
        self,
        landmarks: list,
        eye_indices: list,
        iris_indices: list,
    ) -> float:
        """Ratio of iris center position between left and right eye corners.
        0 = looking fully left, 1 = looking fully right."""
        # eye corners: first = inner, third = outer for right eye (indices 0, 3)
        left_corner = landmarks[eye_indices[0]]
        right_corner = landmarks[eye_indices[3]]
        iris_center = self._centroid(landmarks, iris_indices)

        eye_width = right_corner[0] - left_corner[0]
        if abs(eye_width) < 1e-6:
            return 0.5
        return (iris_center[0] - left_corner[0]) / eye_width

    def _iris_vertical_ratio(
        self,
        landmarks: list,
        eye_indices: list,
        iris_indices: list,
    ) -> float:
        """Ratio of iris vertical position. 0 = top, 1 = bottom."""
        top = landmarks[eye_indices[1]]
        bottom = landmarks[eye_indices[5]]
        iris_center = self._centroid(landmarks, iris_indices)

        eye_height = bottom[1] - top[1]
        if abs(eye_height) < 1e-6:
            return 0.5
        return (iris_center[1] - top[1]) / eye_height

    def _eye_aspect_ratio(self, landmarks: list, eye_indices: list) -> float:
        """EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)"""
        p = [landmarks[i] for i in eye_indices]
        vertical_1 = self._dist(p[1], p[5])
        vertical_2 = self._dist(p[2], p[4])
        horizontal = self._dist(p[0], p[3])
        if horizontal < 1e-6:
            return 0.0
        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def _classify_direction(self, h_ratio: float, v_ratio: float) -> GazeDirection:
        t = EyeMonitorConfig.GAZE_CENTER_THRESHOLD
        if h_ratio < 0.5 - t:
            return GazeDirection.LEFT
        if h_ratio > 0.5 + t:
            return GazeDirection.RIGHT
        if v_ratio < 0.5 - t:
            return GazeDirection.UP
        if v_ratio > 0.5 + t:
            return GazeDirection.DOWN
        return GazeDirection.CENTER

    @staticmethod
    def _centroid(landmarks: list, indices: list) -> Tuple[float, float, float]:
        xs = [landmarks[i][0] for i in indices]
        ys = [landmarks[i][1] for i in indices]
        zs = [landmarks[i][2] for i in indices]
        n = len(indices)
        return (sum(xs) / n, sum(ys) / n, sum(zs) / n)

    @staticmethod
    def _dist(a: Tuple[float, ...], b: Tuple[float, ...]) -> float:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
