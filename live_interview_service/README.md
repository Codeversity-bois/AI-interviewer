# Live Interview Service

AI-powered live interview microservice using Gemini Live API for real-time voice conversations.

## Features

- Real-time voice interview using Gemini Live API
- Automatic transcript generation and display
- Live evaluation of candidate responses
- **Video proctoring with eye tracking and attention monitoring**
- Session management and persistence
- Output generation (JSON file + MongoDB)
- WebSocket-based audio streaming
- WebSocket-based video proctoring

## Environment Variables

Create a `.env` file or set the following environment variables:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Database connections
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=zenith_interviews
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload
```

## Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete testing instructions.

### Quick Test

```bash
# 1. Start the service (Docker or local)
# 2. Run the test script
python3 test_service.py

# Or use the example input directly
curl -X POST http://localhost:8001/session/start \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

### Example Files

- `example_input.json` - Sample candidate data for testing
- `test_service.py` - Automated test script
- `test_docker.sh` - Docker build and test automation

## Running with Docker

### Build the image

**Important**: Build from the parent directory (Gemini_Engine) to include the eye_monitor directory:

```bash
# From the Gemini_Engine directory
docker build -f live_interview_service/Dockerfile -t live-interview-service .
```

This ensures the `eye_monitor` directory and `face_landmarker.task` model file are included for proctoring.

### Run the container

```bash
docker run -d \
  --name live-interview \
  -p 8001:8001 \
  -e GEMINI_API_KEY=your_api_key \
  -e ASTRA_DB_APPLICATION_TOKEN=your_token \
  -e ASTRA_DB_API_ENDPOINT=your_endpoint \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  live-interview-service
```

### Using docker-compose

```yaml
version: '3.8'
services:
  live-interview:
    build: .
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ASTRA_DB_APPLICATION_TOKEN=${ASTRA_DB_APPLICATION_TOKEN}
      - ASTRA_DB_API_ENDPOINT=${ASTRA_DB_API_ENDPOINT}
      - MONGO_URI=${MONGO_URI}
    volumes:
      - ./outputs:/app/outputs
```

## API Endpoints

### REST Endpoints

- `GET /health` - Health check
- `POST /session/start` - Start a new interview session
- `GET /session/{id}/status` - Get session status
- `GET /session/{id}/evaluation` - Get current evaluation
- `POST /session/{id}/end` - End session and get final evaluation

### WebSocket Endpoints

- `WS /session/{id}/live` - Real-time audio streaming
- `WS /session/{id}/video` - Video proctoring with face detection, gaze tracking, and violation detection

## Output

The service generates `output.json` in the service directory containing:
- Complete interview transcript
- Final evaluation scores
- **Proctoring report** (violations, attention scores, face presence metrics)
- Session metadata
- Per-turn evaluations

## Notes

- The service works without AstraDB/MongoDB (falls back to in-memory mode)
- **Proctoring is optional** - if `eye_monitor` module is not available, video endpoint will return an error
- Transcript text is sent in real-time via WebSocket for display
- Audio and text are both generated (response_modalities: ["AUDIO", "TEXT"])
- Proctoring violations are tracked in real-time and included in the final output

## Proctoring Features

The video proctoring system monitors:
- **Face Detection**: Detects if candidate's face is present
- **Multiple Faces**: Detects if multiple people are in frame
- **Gaze Tracking**: Monitors where the candidate is looking (screen vs off-screen)
- **Attention Scoring**: Calculates attention score based on screen focus percentage
- **Violation Detection**: Flags violations when thresholds are exceeded:
  - No face detected for >3 seconds
  - Multiple faces detected for >2 seconds
  - Gaze off-screen for >5 seconds
  - Low attention score (<0.3) over 30-second window

All violations are logged with severity levels (LOW, MEDIUM, HIGH, CRITICAL) and included in the final report.
