"""Pydantic models for the proctoring/eye-monitoring system."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ViolationType(str, Enum):
    NO_FACE = "no_face"
    MULTIPLE_FACES = "multiple_faces"
    GAZE_OFF_SCREEN = "gaze_off_screen"
    LOW_ATTENTION = "low_attention"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GazeDirection(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


class FaceDetectionResult(BaseModel):
    face_present: bool
    face_count: int
    landmarks: Optional[list] = None  # raw landmark list if needed


class GazeResult(BaseModel):
    direction: GazeDirection
    horizontal_ratio: float  # 0=left, 0.5=center, 1=right
    vertical_ratio: float
    is_looking_at_screen: bool
    ear_left: float = 0.0   # eye aspect ratio
    ear_right: float = 0.0


class AttentionScore(BaseModel):
    score: float             # 0.0 to 1.0
    screen_focus_pct: float  # % of time looking at screen in window
    sample_count: int


class Violation(BaseModel):
    type: ViolationType
    severity: Severity
    duration_secs: float
    message: str
    timestamp: float


class FrameAnalysis(BaseModel):
    face: FaceDetectionResult
    gaze: Optional[GazeResult] = None
    attention: Optional[AttentionScore] = None
    violations: List[Violation] = []
    timestamp: float


class ProctoringReport(BaseModel):
    total_frames: int
    total_violations: int
    violations: List[Violation]
    avg_attention_score: float
    screen_focus_pct: float
    face_present_pct: float
