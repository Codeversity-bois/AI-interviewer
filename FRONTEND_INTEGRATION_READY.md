# Live Interview Service - Frontend Integration Guide

## ✅ Microservice Aligned with Frontend

The microservice (`service.py`) has been recreated to **exactly match** the frontend expectations.

### Endpoints (Frontend Compatible)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interview/start` | Start interview session |
| GET | `/interview/{sessionId}/status` | Get session status |
| GET | `/interview/{sessionId}/evaluation` | Get evaluation |
| POST | `/interview/{sessionId}/end` | End session |
| WS | `/interview/{sessionId}/live` | Audio WebSocket (Gemini Live API) |
| WS | `/interview/{sessionId}/video` | Video WebSocket (proctoring) |

### Audio WebSocket Protocol

**Client → Server:**
- **Binary**: Int16 PCM audio (16kHz mono)
- **JSON**: `{"type": "user_transcript", "text": "..."}`

**Server → Client:**
- `{"type": "ready"}` - Connection established
- **Binary**: Int16 PCM audio (24kHz mono) - AI voice
- `{"type": "transcript", "text": "..."}` - AI transcript
- `{"type": "turn_complete"}` - AI finished speaking
- `{"type": "evaluation_update", "evaluation": {...}}` - Live evaluation
- `{"type": "error", "message": "..."}` - Error message

### Video WebSocket Protocol (Proctoring)

**Client → Server:**
- **Binary**: JPEG image blob (from `canvas.toBlob()`)

**Server → Client:**
- `{"type": "proctoring_alert", "alert_type": "...", "message": "...", "severity": "...", ...}`

## 🎯 Proctoring: Backend (Microservice)

**Proctoring is implemented in the MICROSERVICE**, not the frontend.

- **Frontend**: Captures webcam, sends JPEG frames via WebSocket
- **Backend**: Processes frames using `eye_monitor` module (MediaPipe)
  - Face detection
  - Gaze tracking
  - Violation detection (looking away, multiple faces, no face, etc.)
  - Sends alerts back to frontend

### Proctoring Module

Location: `eye_monitor/` (sibling directory to `live_interview_service/`)

Dependencies:
```
opencv-python>=4.8.0
mediapipe>=0.10.0
```

If proctoring is not available, the video WebSocket gracefully closes with code 1011.

## 📦 Request/Response Format

### Start Session Request (POST /interview/start)

```json
{
  "candidate_id": "candidate_12345",
  "job_id": "job_001",
  "job_description": "We are looking for...",
  "skills": ["Python", "React", "AWS"],
  "education": "BS Computer Science, 2020",
  "leetcode_profile": "https://leetcode.com/user",
  "projects": [
    {
      "description": "Built a chat app...",
      "skills": "React, Node.js, WebSocket"
    }
  ]
}
```

### Start Session Response

```json
{
  "session_id": "session_1707321234567",
  "candidate_id": "candidate_12345",
  "job_id": "job_001",
  "started_at": 1707321234.567,
  "is_active": true
}
```

### End Session Response (POST /interview/{sessionId}/end)

```json
{
  "session_id": "session_1707321234567",
  "candidate_id": "candidate_12345",
  "job_id": "job_001",
  "started_at": 1707321234.567,
  "ended_at": 1707321534.567,
  "duration": 300.0,
  "evaluation": {
    "overall_score": 8.5,
    "technical_competency": 9.0,
    "communication_skills": 8.0,
    "recommendation": "hire",
    ...
  },
  "transcript": [
    {"role": "interviewer", "text": "Tell me about yourself"},
    {"role": "candidate", "text": "I'm a software engineer..."}
  ],
  "proctoring": {
    "total_frames": 600,
    "total_violations": 3,
    "violations": [...],
    "avg_attention_score": 0.85,
    "screen_focus_pct": 92.0,
    "face_present_pct": 98.0
  }
}
```

## 🚀 Quick Start

1. **Start microservice:**
```powershell
cd C:\Users\Ameya\Documents\hackathons\iitgn\ai-interviewer\Gemini_Engine
uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload
```

2. **Frontend uses:**
```javascript
INTERVIEW_SERVICE_URL = 'http://localhost:8001'
```

3. **Test endpoints:**
```bash
curl http://localhost:8001/health
```

## ✅ Integration Checklist

- [x] Endpoints match frontend (`/interview/*`)
- [x] Audio WebSocket protocol matches
- [x] Video WebSocket accepts JPEG blobs
- [x] Proctoring alerts format matches
- [x] Response JSON structures match
- [x] Error handling aligned
- [x] Session management compatible

## 🎬 Everything Ready!

The microservice is now **100% aligned** with your frontend. Just start the service and connect your frontend!
