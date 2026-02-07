"""WebSocket handler for receiving webcam frames and streaming proctoring events."""

import base64
import time
import json

import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from eye_monitor.config import EyeMonitorConfig
from eye_monitor.core.frame_processor import FrameProcessor
from eye_monitor.stream.frame_buffer import FrameBuffer


class VideoStreamHandler:
    """Receives base64-encoded frames over WebSocket, processes them, sends back events."""

    def __init__(self):
        self.processor = FrameProcessor()
        self.buffer = FrameBuffer()
        self._last_process_time = 0.0

    async def handle_ws(self, websocket: WebSocket):
        """Main WebSocket loop: receive frames, process, send violations."""
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_text()
                frame = self._decode_frame(data)
                if frame is None:
                    continue

                now = time.time()
                elapsed_ms = (now - self._last_process_time) * 1000

                if elapsed_ms < EyeMonitorConfig.FRAME_PROCESS_INTERVAL_MS:
                    continue  # skip — too soon

                self._last_process_time = now
                analysis = self.processor.process(frame, now)

                # Send back analysis as JSON
                response = {
                    "type": "frame_analysis",
                    "face_present": analysis.face.face_present,
                    "face_count": analysis.face.face_count,
                    "attention_score": analysis.attention.score if analysis.attention else None,
                    "gaze_direction": analysis.gaze.direction.value if analysis.gaze else None,
                    "looking_at_screen": analysis.gaze.is_looking_at_screen if analysis.gaze else None,
                    "violations": [
                        {
                            "type": v.type.value,
                            "severity": v.severity.value,
                            "message": v.message,
                        }
                        for v in analysis.violations
                    ],
                    "timestamp": now,
                }
                await websocket.send_text(json.dumps(response))

        except WebSocketDisconnect:
            pass
        finally:
            self.processor.close()

    def get_report(self):
        return self.processor.get_report()

    @staticmethod
    def _decode_frame(data: str) -> np.ndarray | None:
        """Decode a base64-encoded JPEG/PNG frame to numpy array."""
        try:
            # Strip data URL prefix if present
            if "," in data:
                data = data.split(",", 1)[1]
            raw = base64.b64decode(data)
            arr = np.frombuffer(raw, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None
