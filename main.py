from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import sys
import uuid
import json
import time
import asyncio
import struct
from datetime import datetime
import uvicorn
from dotenv import load_dotenv


load_dotenv(dotenv_path="interview_manager/.env")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="frontend_client"), name="static")

# Try to import resume processing functions, handle import errors
try:
    from resume_processor_rag.core.embeddings_generator import generate_embeddings
    from resume_processor_rag.core.astra_db_manager import insert_embedding_batch
    RESUME_PROCESSING_AVAILABLE = True
    print("Resume processing modules loaded successfully")
except ImportError as e:
    print(f"Warning: Resume processing modules not available: {e}")
    RESUME_PROCESSING_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error initializing resume processing: {e}")
    RESUME_PROCESSING_AVAILABLE = False

# Try to import STT module
try:
    from STT.stt import SpeechToTextProcessor, convert_audio_to_16khz_mono
    STT_AVAILABLE = True
    stt_processor = SpeechToTextProcessor()
    print("STT module loaded successfully")
except ImportError as e:
    print(f"Warning: STT module not available: {e}")
    STT_AVAILABLE = False
    stt_processor = None
except Exception as e:
    print(f"Warning: Error initializing STT: {e}")
    STT_AVAILABLE = False
    stt_processor = None

# Try to import MongoDB manager
try:
    from db.mongo_manager import save_interview_result, save_qa_evaluation, get_interview_result
    MONGO_AVAILABLE = True
    print("MongoDB module loaded successfully")
except ImportError as e:
    print(f"Warning: MongoDB module not available: {e}")
    MONGO_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error initializing MongoDB: {e}")
    MONGO_AVAILABLE = False

# Try to import interview modules
try:
    from interview_manager.core.session_manager import SessionManager
    from interview_manager.core.interview_orchestrator import InterviewOrchestrator
    from eye_monitor.stream.video_stream_handler import VideoStreamHandler
    INTERVIEW_AVAILABLE = True
    print("Interview modules loaded successfully")
except ImportError as e:
    print(f"Warning: Interview modules not available: {e}")
    INTERVIEW_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error initializing interview modules: {e}")
    INTERVIEW_AVAILABLE = False

# Global session manager
session_manager = SessionManager() if INTERVIEW_AVAILABLE else None

# --- Response models ---

class ResumeProcessResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    chunks_processed: Optional[int] = None
    processing_time: Optional[float] = None


class ResumeJSONRequest(BaseModel):
    """JSON resume input — sections of resume text keyed by section type."""
    user_id: Optional[str] = None
    username: Optional[str] = "user"
    sections: dict  # e.g. {"experience": "...", "projects": "...", "skills": "..."}


class InterviewStartRequest(BaseModel):
    user_id: str
    resume_context: Optional[str] = ""


class InterviewStartResponse(BaseModel):
    success: bool
    session_id: str
    message: str
    ws_url: str


class InterviewResponseRequest(BaseModel):
    text: str


# --- Health / test endpoints ---

@app.get("/")
async def root():
    return {"message": "Running"}


@app.get("/health")
async def health():
    return {"message": "OK"}


@app.get("/test")
async def test():
    return {
        "message": "Server is running",
        "resume_processing_available": RESUME_PROCESSING_AVAILABLE,
        "interview_available": INTERVIEW_AVAILABLE,
        "active_sessions": session_manager.active_count if session_manager else 0,
        "cors_enabled": True,
    }


# --- Resume processing ---

@app.post("/resume/process")
async def resume_process(request: ResumeJSONRequest):
    """Process resume data from JSON and store embeddings in Astra DB.

    Expects a JSON body with a `sections` dict, e.g.:
    {
        "username": "john_doe",
        "sections": {
            "experience": "Software Engineer at Acme Corp...",
            "projects": "Built a distributed cache...",
            "education": "B.S. Computer Science...",
            "skills": "Python, Go, Kubernetes..."
        }
    }
    """
    if not RESUME_PROCESSING_AVAILABLE:
        return ResumeProcessResponse(
            success=True,
            message="Resume received (Astra DB not configured - test mode)",
            user_id=request.user_id or "test-user-123",
            chunks_processed=0,
            processing_time=0.1,
        )

    start_time = datetime.now()
    user_id = request.user_id or str(uuid.uuid4())

    try:
        if not request.sections:
            raise HTTPException(status_code=400, detail="sections dict is required and must not be empty")

        json_data = []
        chunk_id = 0
        for section_type, content in request.sections.items():
            if not content or not content.strip():
                continue
            chunk_id += 1
            embeddings = generate_embeddings(content.strip())
            data = {
                "user_id": user_id,
                "username": request.username or "user",
                "chunk_id": chunk_id,
                "section_type": section_type.upper(),
                "content": content.strip(),
                "$vector": embeddings.tolist(),
                "created_at": datetime.now().isoformat(),
            }
            json_data.append(data)

        if not json_data:
            raise HTTPException(status_code=400, detail="No non-empty sections provided")

        insert_embedding_batch(json_data)
        processing_time = (datetime.now() - start_time).total_seconds()

        return ResumeProcessResponse(
            success=True,
            message="Resume processed successfully",
            user_id=user_id,
            chunks_processed=len(json_data),
            processing_time=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        return ResumeProcessResponse(
            success=False,
            message=f"Error processing resume: {str(e)}",
            processing_time=processing_time,
        )


# --- Interview endpoints ---

@app.post("/interview/start", response_model=InterviewStartResponse)
async def interview_start(request: InterviewStartRequest):
    """Create a new interview session."""
    if not INTERVIEW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Interview modules not available")

    state = session_manager.create_session(
        user_id=request.user_id,
        resume_context=request.resume_context or "",
    )

    return InterviewStartResponse(
        success=True,
        session_id=state.session.session_id,
        message="Interview session created",
        ws_url=f"/interview/{state.session.session_id}/ws",
    )


@app.post("/interview/{session_id}/respond")
async def interview_respond(session_id: str, request: InterviewResponseRequest):
    """Process a user response via REST (non-WebSocket flow)."""
    if not INTERVIEW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Interview modules not available")

    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator = InterviewOrchestrator(state)
    ai_response = await orchestrator.on_user_speech(request.text)

    return {
        "success": True,
        "ai_response": ai_response,
        "phase": state.current_phase.value,
        "questions_asked": state.session.total_questions,
    }


@app.get("/interview/{session_id}/status")
async def interview_status(session_id: str):
    """Get current interview status."""
    if not INTERVIEW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Interview modules not available")

    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return state.to_dict()


@app.post("/interview/{session_id}/end")
async def interview_end(session_id: str):
    """End an interview session and get the summary. Results are also saved to MongoDB."""
    if not INTERVIEW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Interview modules not available")

    summary = session_manager.end_session(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    summary_dict = summary.model_dump()

    # Save to MongoDB
    mongo_id = None
    if MONGO_AVAILABLE:
        mongo_id = save_interview_result(summary_dict)

    return {"success": True, "summary": summary_dict, "mongo_id": mongo_id}


# --- WebSocket: Interview conversation ---

@app.websocket("/interview/{session_id}/ws")
async def interview_ws(websocket: WebSocket, session_id: str):
    """Bidirectional WebSocket for real-time interview conversation."""
    if not INTERVIEW_AVAILABLE:
        await websocket.close(code=1011, reason="Interview modules not available")
        return

    state = session_manager.get_session(session_id)
    if not state:
        await websocket.close(code=1008, reason="Session not found")
        return

    await websocket.accept()
    orchestrator = InterviewOrchestrator(state)

    # Send callback: push AI messages to WebSocket
    async def send_ai_message(text):
        await websocket.send_text(json.dumps({"type": "ai_message", "text": text}))

    async def send_backchannel(text):
        await websocket.send_text(json.dumps({"type": "backchannel", "text": text}))

    async def send_violation(violation):
        await websocket.send_text(json.dumps({
            "type": "violation",
            "violation_type": violation.type.value,
            "severity": violation.severity.value,
            "message": violation.message,
        }))

    orchestrator.set_callbacks(
        on_ai_message=send_ai_message,
        on_backchannel=send_backchannel,
        on_violation=send_violation,
    )

    # Start the interview
    opening = orchestrator.start()
    await websocket.send_text(json.dumps({
        "type": "ai_message",
        "text": opening,
        "phase": state.current_phase.value,
    }))

    try:
        while state.session.is_active:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "user_text":
                response = await orchestrator.on_user_speech(msg["text"])
                if response:
                    await websocket.send_text(json.dumps({
                        "type": "ai_message",
                        "text": response,
                        "phase": state.current_phase.value,
                        "questions_asked": state.session.total_questions,
                    }))

            elif msg.get("type") == "audio_chunk":
                import base64
                audio = base64.b64decode(msg["data"])
                # Transcribe audio via STT and feed text to orchestrator
                if STT_AVAILABLE and stt_processor:
                    result = await stt_processor.process_audio_data(audio)
                    if result.get("success") and result.get("transcript", "").strip():
                        transcript_text = result["transcript"].strip()
                        response = await orchestrator.on_user_speech(transcript_text)
                        if response:
                            await websocket.send_text(json.dumps({
                                "type": "ai_message",
                                "text": response,
                                "phase": state.current_phase.value,
                                "questions_asked": state.session.total_questions,
                            }))

            elif msg.get("type") == "end_interview":
                result = orchestrator.end_interview()
                # Save to MongoDB
                if MONGO_AVAILABLE:
                    save_interview_result(result)
                await websocket.send_text(json.dumps({
                    "type": "interview_ended",
                    "summary": result,
                }))
                break

    except WebSocketDisconnect:
        orchestrator.end_interview()
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        orchestrator.end_interview()


# --- WebSocket: Video proctoring ---

@app.websocket("/interview/{session_id}/video")
async def interview_video(websocket: WebSocket, session_id: str):
    """WebSocket for webcam frames — proctoring pipeline."""
    if not INTERVIEW_AVAILABLE:
        await websocket.close(code=1011, reason="Interview modules not available")
        return

    state = session_manager.get_session(session_id)
    if not state:
        await websocket.close(code=1008, reason="Session not found")
        return

    handler = VideoStreamHandler()
    await handler.handle_ws(websocket)

    # After disconnect, log violations into session state
    report = handler.get_report()
    for v in report.violations:
        state.add_violation(v)


# --- STT endpoints ---

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe an audio file (WAV, MP3, OGG, WebM) to text using AssemblyAI."""
    if not STT_AVAILABLE:
        raise HTTPException(status_code=503, detail="STT module not available")

    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {file.content_type}")

    audio_data = await file.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="Empty audio file")

    processed_audio = convert_audio_to_16khz_mono(audio_data)
    result = await stt_processor.process_audio_data(processed_audio)

    if result["success"]:
        return {"transcript": result["transcript"]}
    else:
        raise HTTPException(status_code=500, detail=result["error"])


# --- Legacy endpoint ---

@app.post("/session/start")
async def session_start():
    return {"message": "Use /interview/start instead."}


# --- Gemini Live API proxy ---

try:
    from google import genai
    GENAI_AVAILABLE = True
    print("google-genai loaded for Live API")
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not available for Live API")

LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"


def _build_live_system_prompt(resume_context: str = "") -> str:
    resume = resume_context.strip() if resume_context else "No resume provided."
    return (
        "You are Zenith — a professional AI interviewer conducting a real job interview.\n\n"
        "INTERVIEW CONDUCT:\n"
        "- Ask ONE question at a time\n"
        "- Keep questions concise (1-2 sentences)\n"
        "- Sound natural — like a real human interviewer, not a quiz bot\n"
        "- When the candidate mentions a technology choice, ask WHY they chose it\n"
        "- Probe for depth — surface-level answers should trigger follow-ups\n"
        "- Be professional but conversational\n"
        "- Adapt difficulty to the candidate's level\n\n"
        "INTERVIEW FLOW:\n"
        "1. Greet the candidate and ask them to introduce themselves\n"
        "2. Ask behavioral questions (teamwork, leadership, challenges)\n"
        "3. Ask technical questions based on their resume skills\n"
        "4. Deep-dive into their projects (architecture, decisions, results)\n"
        "5. Wrap up — ask if they have questions, thank them\n\n"
        "NATURAL CONVERSATION:\n"
        "- If the candidate is thinking (hmm, uhh, let me think), wait patiently\n"
        "- If they ask for clarification, provide it naturally\n"
        "- React briefly to answers before asking the next question\n"
        "- Use natural transitions — reference what they just said\n\n"
        f"CANDIDATE RESUME:\n{resume}\n\n"
        "Begin the interview by greeting the candidate."
    )


@app.websocket("/interview/live")
async def interview_live_ws(websocket: WebSocket):
    """WebSocket proxy: browser audio <-> Gemini Live API.

    Protocol:
        Client sends:
            - JSON: {"type": "config", "resume_context": "..."}  (first message)
            - Binary: raw 16-bit PCM audio frames at 16 kHz mono
            - JSON: {"type": "end"}
        Server sends:
            - JSON: {"type": "ready"}
            - Binary: raw 16-bit PCM audio at 24 kHz mono (Gemini response)
            - JSON: {"type": "transcript", "text": "..."}  (when text is available)
            - JSON: {"type": "turn_complete"}
            - JSON: {"type": "error", "message": "..."}
    """
    if not GENAI_AVAILABLE:
        await websocket.close(code=1011, reason="google-genai not available")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        await websocket.close(code=1011, reason="GEMINI_API_KEY not set")
        return

    await websocket.accept()

    # Wait for config message
    try:
        first_msg = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        config_data = json.loads(first_msg)
        resume_context = config_data.get("resume_context", "")
    except Exception:
        resume_context = ""

    client = genai.Client(api_key=api_key)
    live_config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": _build_live_system_prompt(resume_context),
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Puck"
                }
            }
        },
    }

    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=live_config) as session:
            await websocket.send_text(json.dumps({"type": "ready"}))

            stop_event = asyncio.Event()

            async def forward_browser_audio():
                """Read PCM from browser WebSocket, send to Gemini."""
                try:
                    while not stop_event.is_set():
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.receive":
                            if "bytes" in msg and msg["bytes"]:
                                await session.send_realtime_input(
                                    audio={"data": msg["bytes"], "mime_type": "audio/pcm"}
                                )
                            elif "text" in msg and msg["text"]:
                                data = json.loads(msg["text"])
                                if data.get("type") == "end":
                                    stop_event.set()
                                    return
                        elif msg["type"] == "websocket.disconnect":
                            stop_event.set()
                            return
                except WebSocketDisconnect:
                    stop_event.set()

            async def forward_gemini_audio():
                """Read audio from Gemini, send to browser WebSocket."""
                try:
                    while not stop_event.is_set():
                        turn = session.receive()
                        async for response in turn:
                            if stop_event.is_set():
                                return
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                                        await websocket.send_bytes(part.inline_data.data)
                                    elif part.text:
                                        await websocket.send_text(json.dumps({
                                            "type": "transcript",
                                            "text": part.text
                                        }))
                            if response.server_content and response.server_content.turn_complete:
                                await websocket.send_text(json.dumps({"type": "turn_complete"}))
                except Exception as e:
                    if not stop_event.is_set():
                        try:
                            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                        except Exception:
                            pass
                    stop_event.set()

            await asyncio.gather(
                forward_browser_audio(),
                forward_gemini_audio(),
                return_exceptions=True,
            )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
