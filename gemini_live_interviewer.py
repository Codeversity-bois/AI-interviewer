"""
Gemini Live API Interviewer — Real-time voice interview using mic streaming.

Handles both STT and TTS natively through Gemini's Live API.
No need for separate AssemblyAI / TTS services.

Usage:
    python gemini_live_interviewer.py
    python gemini_live_interviewer.py --resume "3 years Python, built microservices at Acme Corp"
"""

import asyncio
import argparse
import os

from google import genai
from dotenv import load_dotenv

try:
    import pyaudio
except ImportError:
    print("pyaudio is required. Install it with: pip install pyaudio")
    print("On Linux you may also need: sudo apt-get install portaudio19-dev")
    exit(1)

load_dotenv(dotenv_path="interview_manager/.env")

# ── Audio config ──────────────────────────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

# ── Gemini Live config ────────────────────────────────────────────────────────
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"


def build_system_prompt(resume_context: str = "") -> str:
    """Build the interviewer system prompt."""
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


async def run_interview(resume_context: str = ""):
    """Main interview loop using Gemini Live API with mic streaming."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Set it in interview_manager/.env")
        return

    client = genai.Client(api_key=api_key)
    pya = pyaudio.PyAudio()

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": build_system_prompt(resume_context),
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Puck"
                }
            }
        },
    }

    audio_out_queue = asyncio.Queue()
    audio_in_queue = asyncio.Queue(maxsize=5)
    mic_stream = None

    async def listen_mic():
        """Capture mic audio and queue it for sending."""
        nonlocal mic_stream
        mic_info = pya.get_default_input_device_info()
        mic_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        while True:
            data = await asyncio.to_thread(mic_stream.read, CHUNK_SIZE, **kwargs)
            await audio_in_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def send_audio(session):
        """Stream mic audio to Gemini."""
        while True:
            msg = await audio_in_queue.get()
            await session.send_realtime_input(audio=msg)

    async def receive_audio(session):
        """Receive Gemini audio responses and queue for playback."""
        while True:
            turn = session.receive()
            async for response in turn:
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data and isinstance(part.inline_data.data, bytes):
                            audio_out_queue.put_nowait(part.inline_data.data)

            # Clear queue on interruption (user started speaking)
            while not audio_out_queue.empty():
                audio_out_queue.get_nowait()

    async def play_audio():
        """Play Gemini's audio responses through speakers."""
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            data = await audio_out_queue.get()
            await asyncio.to_thread(stream.write, data)

    # ── Connect and run ───────────────────────────────────────────────────────
    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("=" * 60)
            print("  Gemini Live Interviewer — Connected!")
            print("  Speak into your mic. Use headphones to avoid echo.")
            print("  Press Ctrl+C to end the interview.")
            print("=" * 60)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(listen_mic())
                tg.create_task(send_audio(session))
                tg.create_task(receive_audio(session))
                tg.create_task(play_audio())

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\nConnection error: {e}")
    finally:
        if mic_stream:
            mic_stream.close()
        pya.terminate()
        print("\nInterview ended. Goodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Live AI Interviewer")
    parser.add_argument(
        "--resume", type=str, default="",
        help="Resume context string (e.g. '3 years Python, React, AWS')"
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_interview(resume_context=args.resume))
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
