# Frontend Testing Instructions

## Quick Start

### 1. Start Microservice

From `Gemini_Engine` directory:
```powershell
uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Serve Frontend

From `frontend_client` directory:
```powershell
python -m http.server 8080
```

### 3. Open Browser

Navigate to: **http://localhost:8080/live_interview.html**

## Configuration

✅ **Already configured correctly:**
- API URL: `http://localhost:8001`
- WebSocket URL: `ws://localhost:8001`
- All endpoints match microservice

**No changes needed!**

## Testing Flow

1. Fill out the form with candidate data
2. Click "Start Live Interview"
3. Grant microphone and camera permissions
4. Speak - AI will respond
5. Watch transcript appear
6. See proctoring alerts (if violations)
7. Click "End" button
8. View results with scores and transcript

## Files

- `live_interview.html` - Main interview page
- `live_interview_app.js` - Frontend logic (already configured for port 8001)

See `../live_interview_service/FRONTEND_TESTING_GUIDE.md` for detailed instructions.
