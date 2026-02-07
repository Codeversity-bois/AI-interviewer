"""Eye monitor configuration — thresholds and tuning constants."""


class EyeMonitorConfig:
    # Face detection
    FACE_DETECTION_CONFIDENCE = 0.5
    FACE_MESH_CONFIDENCE = 0.5

    # Gaze thresholds
    GAZE_CENTER_THRESHOLD = 0.35       # iris ratio within this = looking at screen
    EAR_BLINK_THRESHOLD = 0.2          # eye aspect ratio below this = blink

    # Attention scoring
    SLIDING_WINDOW_SECS = 30
    MIN_ATTENTION_SCORE = 0.3          # below this = violation

    # Violation rules
    FACE_ABSENCE_LIMIT_SECS = 3.0
    GAZE_OFF_SCREEN_LIMIT_SECS = 5.0
    MULTIPLE_FACES_LIMIT_SECS = 2.0

    # Processing
    FRAME_PROCESS_INTERVAL_MS = 200    # process every 200ms (5 fps)
    FRAME_BUFFER_SIZE = 30             # ring buffer capacity
