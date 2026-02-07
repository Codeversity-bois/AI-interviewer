"""
Live Interview Microservice — Gemini Live API powered.

Run standalone:
    uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload

Endpoints (matching frontend):
    POST   /interview/start                — Start interview session
    GET    /interview/{id}/status          — Get session status
    GET    /interview/{id}/evaluation      — Get evaluation
    POST   /interview/{id}/end             — End session
    WS     /interview/{id}/live            — Audio WebSocket (browser <-> Gemini Live)
    WS     /interview/{id}/video           — Video WebSocket (proctoring)
    GET    /health                         — Health check
"""

import os
import json
import time
import asyncio
from typing import Dict, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from google import genai

from live_interview_service.config import GEMINI_API_KEY, LIVE_MODEL, VOICE_NAME
from live_interview_service.models import CandidateInput, InterviewSession, TranscriptTurn
from live_interview_service.candidate_store import ingest_candidate, get_candidate_context
from live_interview_service.evaluator import LiveEvaluator
from live_interview_service.prompts import build_interviewer_prompt


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Zenith Live Interview Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend if available
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend_client")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# ── In-memory session store ──────────────────────────────────────────────────

_sessions: Dict[str, InterviewSession] = {}
_evaluators: Dict[str, LiveEvaluator] = {}
_candidate_contexts: Dict[str, str] = {}
_job_descriptions: Dict[str, str] = {}


# ── Helper: Save output JSON ──────────────────────────────────────────────────

def _save_output_json(session_id: str, data: dict):
    """Save interview output to JSON file in microservice directory."""
    output_path = os.path.join(os.path.dirname(__file__), f"output_{session_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Service] Saved interview output to: {output_path}")


# ── REST Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "live-interview",
        "active_sessions": len([s for s in _sessions.values() if s.is_active]),
        "gemini_key_set": bool(GEMINI_API_KEY),
    }


@app.post("/interview/start")
async def start_interview(payload: CandidateInput):
    """Start a new interview session.
    
    Frontend expects:
        - POST /interview/start
        - Body: CandidateInput JSON
        - Response: { session_id, candidate_id, job_id, started_at, is_active }
    """
    session_id = f"session_{int(time.time() * 1000)}"
    
    # Ingest candidate data
    try:
        ingest_candidate(payload)
        context_text = get_candidate_context(payload.candidate_id, query="", limit=10)
    except Exception as e:
        print(f"[Service] Warning: Failed to ingest candidate: {e}")
        context_text = ""
    
    # Create session
    session = InterviewSession(
        session_id=session_id,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        started_at=time.time(),
        is_active=True,
    )
    
    _sessions[session_id] = session
    _candidate_contexts[session_id] = context_text
    _job_descriptions[session_id] = payload.job_description
    
    # Create evaluator (matching LiveEvaluator constructor)
    evaluator = LiveEvaluator(
        session_id=session_id,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        job_description=payload.job_description,
    )
    _evaluators[session_id] = evaluator
    
    print(f"[Service] Started session {session_id} for candidate {payload.candidate_id}")
    
    return {
        "session_id": session_id,
        "candidate_id": payload.candidate_id,
        "job_id": payload.job_id,
        "started_at": session.started_at,
        "is_active": session.is_active,
    }


@app.get("/interview/{session_id}/status")
async def get_status(session_id: str):
    """Get session status.
    
    Frontend expects:
        - GET /interview/{session_id}/status
        - Response: { session_id, is_active, started_at, ended_at, duration, transcript_length }
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    duration = (session.ended_at or time.time()) - session.started_at
    
    return {
        "session_id": session_id,
        "is_active": session.is_active,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration": duration,
        "transcript_length": len(session.transcript),
    }


@app.get("/interview/{session_id}/evaluation")
async def get_evaluation(session_id: str):
    """Get current evaluation.
    
    Frontend expects:
        - GET /interview/{session_id}/evaluation
        - Response: evaluation JSON object
    """
    evaluator = _evaluators.get(session_id)
    if not evaluator:
        raise HTTPException(status_code=404, detail="Evaluator not found")
    
    return evaluator.get_evaluation_snapshot()


@app.post("/interview/{session_id}/end")
async def end_interview(session_id: str):
    """End interview session and return final evaluation.
    
    Frontend expects:
        - POST /interview/{session_id}/end
        - Response: { session_id, evaluation, transcript, proctoring }
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.ended_at = time.time()
    
    # Finalize evaluation
    evaluator = _evaluators.get(session_id)
    if evaluator:
        final_eval = await evaluator.finalize()
    else:
        final_eval = None
    
    # Prepare output
    output_data = {
        "session_id": session_id,
        "candidate_id": session.candidate_id,
        "job_id": session.job_id,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration": session.ended_at - session.started_at,
        "evaluation": final_eval.model_dump() if final_eval else None,
        "transcript": [t.model_dump() for t in session.transcript],
        "proctoring": session.proctoring_report,
    }
    
    # Save to file
    _save_output_json(session_id, output_data)
    
    return output_data


# ── WebSocket: Audio (Gemini Live API) ───────────────────────────────────────

@app.websocket("/interview/{session_id}/live")
async def audio_websocket(websocket: WebSocket, session_id: str):
    """Audio WebSocket for live interview with Gemini Live API.
    
    Frontend protocol:
        Client sends:
            - Binary: raw Int16 PCM audio (16kHz mono)
            - JSON: {"type": "user_transcript", "text": "..."}
        
        Server sends:
            - JSON: {"type": "ready"}
            - Binary: raw Int16 PCM audio (24kHz mono) from Gemini
            - JSON: {"type": "transcript", "text": "..."}
            - JSON: {"type": "turn_complete"}
            - JSON: {"type": "evaluation_update", "evaluation": {...}}
            - JSON: {"type": "error", "message": "..."}
    """
    session = _sessions.get(session_id)
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    if not GEMINI_API_KEY:
        await websocket.close(code=1011, reason="GEMINI_API_KEY not set")
        return
    
    await websocket.accept()
    
    evaluator = _evaluators.get(session_id)
    context_text = _candidate_contexts.get(session_id, "")
    job_desc = _job_descriptions.get(session_id, "")
    
    # Build system prompt
    prompt_text = build_interviewer_prompt(job_desc or "", context_text or "")
    
    if not prompt_text or not prompt_text.strip():
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Invalid session: missing job description"
        }))
        await websocket.close(code=1008, reason="Invalid session data")
        return
    
    # Create Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Gemini Live config
    live_config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": prompt_text.strip(),
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": VOICE_NAME,
                }
            }
        },
    }
    
    try:
        print(f"[Live] Connecting to {LIVE_MODEL} for session {session_id}")
        
        async with client.aio.live.connect(model=LIVE_MODEL, config=live_config) as gemini:
            await websocket.send_text(json.dumps({"type": "ready"}))
            stop = asyncio.Event()
            
            # Track AI responses for evaluation
            current_ai_text = ""
            last_question = ""
            
            async def browser_to_gemini():
                """Forward browser audio to Gemini."""
                try:
                    while not stop.is_set():
                        msg = await websocket.receive()
                        
                        if msg["type"] == "websocket.receive":
                            if "bytes" in msg and msg["bytes"]:
                                # Audio data - forward to Gemini
                                await gemini.send_realtime_input(
                                    audio={"data": msg["bytes"], "mime_type": "audio/pcm"}
                                )
                            elif "text" in msg and msg["text"]:
                                # JSON control message
                                try:
                                    data = json.loads(msg["text"])
                                    if data.get("type") == "user_transcript":
                                        # Frontend sends user transcript
                                        user_text = data.get("text", "")
                                        if user_text.strip():
                                            session.transcript.append(
                                                TranscriptTurn(role="candidate", text=user_text)
                                            )
                                            if evaluator:
                                                evaluator.add_turn("candidate", user_text)
                                                if last_question:
                                                    asyncio.create_task(
                                                        evaluator.evaluate_turn(last_question, user_text)
                                                    )
                                except json.JSONDecodeError:
                                    pass
                        elif msg["type"] == "websocket.disconnect":
                            stop.set()
                            return
                except WebSocketDisconnect:
                    stop.set()
            
            async def gemini_to_browser():
                """Forward Gemini responses to browser."""
                nonlocal current_ai_text, last_question
                
                try:
                    while not stop.is_set():
                        turn = gemini.receive()
                        async for response in turn:
                            if stop.is_set():
                                return
                            
                            sc = response.server_content
                            if sc and sc.model_turn:
                                for part in sc.model_turn.parts:
                                    # Audio data
                                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                                        await websocket.send_bytes(part.inline_data.data)
                                    
                                    # Text transcript
                                    elif part.text:
                                        current_ai_text += part.text
                                        await websocket.send_text(json.dumps({
                                            "type": "transcript",
                                            "text": part.text,
                                        }))
                            
                            if sc and sc.turn_complete:
                                # AI finished speaking
                                if current_ai_text.strip():
                                    session.transcript.append(
                                        TranscriptTurn(role="interviewer", text=current_ai_text.strip())
                                    )
                                    last_question = current_ai_text.strip()
                                    if evaluator:
                                        evaluator.add_turn("interviewer", last_question)
                                    current_ai_text = ""
                                
                                await websocket.send_text(json.dumps({"type": "turn_complete"}))
                                
                                # Send evaluation update
                                if evaluator:
                                    await websocket.send_text(json.dumps({
                                        "type": "evaluation_update",
                                        "evaluation": evaluator.get_evaluation_snapshot(),
                                    }))
                
                except Exception as e:
                    if not stop.is_set():
                        print(f"[Live] Gemini error: {e}")
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": str(e),
                            }))
                        except:
                            pass
                    stop.set()
            
            await asyncio.gather(
                browser_to_gemini(),
                gemini_to_browser(),
                return_exceptions=True,
            )
    
    except Exception as connect_error:
        error_msg = str(connect_error)
        error_type = type(connect_error).__name__
        print(f"[Live] ❌ Connection error: {error_type}: {error_msg}")
        import traceback
        traceback.print_exc()
        
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to connect to Gemini: {error_msg}"
            }))
        except:
            pass
        return
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[Live] WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session.is_active:
            session.is_active = False
            session.ended_at = time.time()


# ── WebSocket: Video (Proctoring) ────────────────────────────────────────────

@app.websocket("/interview/{session_id}/video")
async def video_websocket(websocket: WebSocket, session_id: str):
    """Video WebSocket for proctoring.
    
    Frontend protocol:
        Client sends:
            - Binary: JPEG image blob (canvas.toBlob)
        
        Server sends:
            - JSON: {"type": "proctoring_alert", "alert_type": "...", "message": "...", "severity": "..."}
    """
    session = _sessions.get(session_id)
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    try:
        # Import proctoring modules
        from eye_monitor.stream.video_stream_handler import VideoStreamHandler
        from eye_monitor.config import EyeMonitorConfig
        import cv2
        import numpy as np
        
        handler = VideoStreamHandler()
        await websocket.accept()
        print(f"[Video] Proctoring started for session {session_id}")
        
        try:
            while True:
                msg = await websocket.receive()
                frame = None
                
                # Handle binary JPEG blob from frontend
                if "bytes" in msg and msg["bytes"]:
                    try:
                        arr = np.frombuffer(msg["bytes"], dtype=np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    except Exception as e:
                        print(f"[Video] Failed to decode frame: {e}")
                        continue
                
                if frame is not None:
                    now = time.time()
                    elapsed_ms = (now - handler._last_process_time) * 1000
                    if elapsed_ms < EyeMonitorConfig.FRAME_PROCESS_INTERVAL_MS:
                        continue
                    
                    handler._last_process_time = now
                    analysis = handler.processor.process(frame, now)
                    
                    # Only send alert if there are actual violations
                    if analysis.violations:
                        # Send proctoring alert (matching frontend format)
                        response = {
                            "type": "proctoring_alert",
                            "alert_type": analysis.violations[0].type.value,
                            "message": analysis.violations[0].message,
                            "severity": analysis.violations[0].severity.value,
                            "timestamp": now,
                            "face_present": analysis.face.face_present,
                            "face_count": analysis.face.face_count,
                            "gaze_direction": analysis.gaze.direction.value if analysis.gaze else None,
                            "looking_at_screen": analysis.gaze.is_looking_at_screen if analysis.gaze else None,
                            "attention_score": analysis.attention.score if analysis.attention else None,
                        }
                        await websocket.send_text(json.dumps(response))
        
        finally:
            # Save proctoring report
            try:
                handler.processor.close()
            except AttributeError:
                pass  # No close method
            
            report = handler.get_report()
            if report:
                session.proctoring_report = {
                    "total_frames": report.total_frames,
                    "total_violations": report.total_violations,
                    "violations": [v.model_dump() for v in report.violations],
                    "avg_attention_score": report.avg_attention_score,
                    "screen_focus_pct": report.screen_focus_pct,
                    "face_present_pct": report.face_present_pct,
                }
                print(f"[Video] Proctoring report saved: {report.total_violations} violations")
    
    except ImportError as e:
        print(f"[Video] Proctoring module not available: {e}")
        print("[Video] Please install: pip install opencv-python mediapipe")
        await websocket.close(code=1011, reason="Proctoring module not available")
    except WebSocketDisconnect:
        print(f"[Video] Proctoring disconnected for session {session_id}")
    except Exception as e:
        print(f"[Video] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close(code=1011, reason=f"Video error: {str(e)}")
        except:
            pass
