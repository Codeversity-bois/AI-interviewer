"""Face detection using MediaPipe FaceLandmarker (tasks API)."""

import os
import cv2
import numpy as np
import mediapipe as mp

from eye_monitor.config import EyeMonitorConfig
from eye_monitor.models.proctoring_events import FaceDetectionResult

# Path to the downloaded face landmarker model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "face_landmarker.task")

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


class FaceDetector:
    """Detects faces and extracts landmarks via MediaPipe FaceLandmarker."""

    def __init__(self):
        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.IMAGE,
            num_faces=2,  # detect up to 2 to catch cheating
            min_face_detection_confidence=EyeMonitorConfig.FACE_DETECTION_CONFIDENCE,
            min_tracking_confidence=EyeMonitorConfig.FACE_MESH_CONFIDENCE,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)

    def detect(self, frame: np.ndarray) -> FaceDetectionResult:
        """Run face landmarker on a BGR frame. Returns detection result."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        if not result.face_landmarks:
            return FaceDetectionResult(
                face_present=False, face_count=0, landmarks=None
            )

        face_count = len(result.face_landmarks)
        # First face's landmarks as list of (x, y, z)
        landmarks = [
            (lm.x, lm.y, lm.z) for lm in result.face_landmarks[0]
        ]

        return FaceDetectionResult(
            face_present=True,
            face_count=face_count,
            landmarks=landmarks,
        )

    def close(self):
        self._landmarker.close()
