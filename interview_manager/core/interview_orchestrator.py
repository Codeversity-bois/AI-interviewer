"""Main interview orchestrator — wires up all modules and drives the interview."""

import os
import asyncio
import random
from typing import Optional, Callable

from google import genai
from google.genai import types
from dotenv import load_dotenv

from interview_manager.config import InterviewPhase, InterviewConfig
from interview_manager.core.interview_state import InterviewState
from interview_manager.core.question_strategy import QuestionStrategy
from answer_verifier.core.verification_pipeline import VerificationPipeline
from answer_verifier.models.verification_models import FollowupQuestion
from conversation_intelligence.core.speech_state_machine import SpeechStateMachine
from conversation_intelligence.core.turn_manager import TurnManager
from conversation_intelligence.core.silence_detector import SilenceDetector
from conversation_intelligence.core.interrupt_controller import InterruptController
from conversation_intelligence.core.backchanneling import BackchannelEngine
from conversation_intelligence.models.conversation_states import SpeechEvent
from eye_monitor.core.frame_processor import FrameProcessor
from eye_monitor.models.proctoring_events import FrameAnalysis
try:
    from resume_processor_rag.core.astra_db_manager import get_candidate_context
except ImportError:
    get_candidate_context = None

try:
    from db.mongo_manager import save_qa_evaluation
except ImportError:
    save_qa_evaluation = None

load_dotenv(dotenv_path="interview_manager/.env")

# Phase-specific system prompts
PHASE_PROMPTS = {
    InterviewPhase.INTRO: (
        "You are starting the interview. Greet the candidate professionally, introduce yourself as "
        "Zenith, and ask them to briefly introduce themselves. Keep it warm but professional — "
        "like a real human interviewer would."
    ),
    InterviewPhase.BEHAVIORAL: (
        "Ask behavioral questions about teamwork, leadership, conflict resolution, and "
        "time management. Use the STAR method framework. Base questions on their resume. "
        "Listen carefully and ask natural follow-ups based on what they actually say."
    ),
    InterviewPhase.TECHNICAL: (
        "Ask technical questions relevant to the candidate's skills listed in their resume. "
        "Start with fundamentals and increase difficulty based on their responses. "
        "If they seem to be thinking, give them space before moving on."
    ),
    InterviewPhase.PROJECT_DEEP_DIVE: (
        "Ask detailed questions about the candidate's projects from their resume. "
        "Probe into architecture decisions, technology choices, challenges faced, and results. "
        "If they mention a specific tool or framework, ask WHY they chose it over alternatives."
    ),
    InterviewPhase.WRAP_UP: (
        "Wrap up the interview. Ask if they have any questions for you. Thank them for their time. "
        "Give a brief positive note about something specific they discussed well."
    ),
}


class InterviewOrchestrator:
    """The brain — coordinates interview flow, verification, proctoring, and conversation."""

    def __init__(self, state: InterviewState):
        self.state = state
        self.strategy = QuestionStrategy()
        self.verifier = VerificationPipeline()
        self.speech_fsm = SpeechStateMachine()
        self.turn_manager = TurnManager()
        self.silence_detector = SilenceDetector()
        self.interrupt_ctrl = InterruptController()
        self.backchannel = BackchannelEngine()
        self.frame_processor = FrameProcessor()

        # Gemini chat client
        api_key = os.getenv("GEMINI_API_KEY")
        self._gemini = genai.Client(api_key=api_key)
        self._chat = None

        # Callbacks for sending responses back to the client
        self._on_ai_message: Optional[Callable] = None
        self._on_backchannel: Optional[Callable] = None
        self._on_violation: Optional[Callable] = None

    def set_callbacks(
        self,
        on_ai_message: Callable = None,
        on_backchannel: Callable = None,
        on_violation: Callable = None,
    ):
        """Register callbacks for sending events back to the WebSocket."""
        self._on_ai_message = on_ai_message
        self._on_backchannel = on_backchannel
        self._on_violation = on_violation

    # --- Interview lifecycle ---

    def start(self) -> str:
        """Initialize the chat and send the opening question."""
        system_prompt = self._build_system_prompt()

        self._chat = self._gemini.chats.create(
            model=InterviewConfig.GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=InterviewConfig.TEMPERATURE,
                max_output_tokens=InterviewConfig.MAX_OUTPUT_TOKENS,
            ),
        )

        # Generate opening message
        opening = self._generate_question(
            "Start the interview. Introduce yourself as Zenith, greet the candidate professionally, "
            "and ask them to introduce themselves briefly."
        )
        self.state.add_ai_message(opening)
        self.state.record_question_asked()
        self.speech_fsm.transition(SpeechEvent.AI_RESPONSE_STARTED)
        return opening

    async def on_user_speech(self, text: str) -> Optional[str]:
        """Handle user speech. The interviewer decides when the answer is complete.

        The interviewee may say filler words like 'hmm', 'uhh', think out loud,
        ask for clarification, or answer across multiple speech chunks. All of
        their conversation fragments are stored in the buffer and the interviewer
        only evaluates the answer once it determines the response is complete.
        """
        # 1. Buffer the input — every speech chunk is stored
        self.state.buffer_user_input(text)

        # 2. Add to transcript (raw log of every chunk)
        transcript_idx = self.state.add_user_message(text)
        self.speech_fsm.transition(SpeechEvent.SPEECH_ENDED)

        # 3. Analyze turn intent
        current_q = self.state.current_qa.question if self.state.current_qa else self.state.last_question
        full_buffer = " ".join(self.state._pending_answer_buffer)

        decision = self._analyze_turn(current_q, full_buffer, text)
        print(f"[Orchestrator] Turn Decision: {decision} | Buffer chunks: {len(self.state._pending_answer_buffer)}")

        if decision == "ANSWER_COMPLETE":
            # Finalize Q&A pair — the full buffer becomes the answer
            self.state.finalize_answer()

            # Kick off verification on the FULL answer (not just last chunk)
            self._verify_async(full_buffer, transcript_idx)

            # Generate next question
            return self._decide_and_ask()

        elif decision == "THINKING":
            # User is thinking — vary the backchannel responses
            backchannels = [
                "Take your time.",
                "Sure, no rush.",
                "Of course, think it through.",
            ]
            bc_text = random.choice(backchannels)
            if self._on_backchannel:
                await self._on_backchannel(bc_text)
            return None

        elif decision == "ASKING_CLARIFICATION":
            response = self._generate_question(
                f"The candidate asked for clarification: '{text}'. "
                f"Provide a helpful, brief clarification for the previous question: '{current_q}'. "
                f"Do not ask a new question yet. Keep it natural and conversational."
            )
            self.state.add_ai_message(response)
            return response

        else:
            # PARTIAL — wait for more input, don't respond yet
            return None

    def _analyze_turn(self, question: str, full_answer: str, latest_chunk: str) -> str:
        """Classify the user's turn with awareness of natural speech patterns.

        The interviewer must distinguish between filler words (not answers),
        partial answers, complete answers, and clarification requests.
        """
        # Quick local check: if the latest chunk is purely filler, skip the model call
        filler_patterns = [
            "hmm", "hmmm", "uhh", "uh", "umm", "um", "let me think",
            "one second", "give me a moment", "hold on", "let me see",
            "that's a good question", "interesting question", "okay so",
        ]
        stripped = latest_chunk.strip().lower().rstrip(".,!?")
        if stripped in filler_patterns or len(stripped) < 4:
            return "THINKING"

        prompt = (
            f"You are evaluating whether an interviewee has finished answering a question "
            f"in a live interview. The interviewee may think out loud, say filler words, "
            f"pause, or take time before giving their actual answer.\n\n"
            f"Interview question: {question}\n"
            f"Everything the interviewee has said so far: {full_answer}\n"
            f"Latest thing they said: {latest_chunk}\n\n"
            "Classify the interviewee's state:\n"
            "- ANSWER_COMPLETE: They have given a substantive answer and seem done.\n"
            "- THINKING: They are using filler words (hmm, uhh, let me think), "
            "pausing, or stalling before answering. This is NOT an answer.\n"
            "- ASKING_CLARIFICATION: They are asking you to repeat or clarify the question.\n"
            "- PARTIAL: They started answering but are clearly mid-thought and not done yet.\n\n"
            "IMPORTANT: Filler words and thinking sounds are NEVER an answer. "
            "Only mark ANSWER_COMPLETE when there is real substantive content.\n\n"
            "Return ONLY the category name."
        )
        try:
            resp = self._gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            result = resp.text.strip().upper()
            if result in ("ANSWER_COMPLETE", "THINKING", "ASKING_CLARIFICATION", "PARTIAL"):
                return result
            return "PARTIAL"
        except Exception:
            return "PARTIAL"  # Safer fallback: wait for more input

    def on_frame(self, frame) -> Optional[FrameAnalysis]:
        """Process a webcam frame for proctoring."""
        analysis = self.frame_processor.process(frame)

        # Record violations
        for v in analysis.violations:
            self.state.add_violation(v)
            if self._on_violation:
                self._on_violation(v)

        # Update attention
        if analysis.attention:
            self.state.update_attention(analysis.attention.score)

        return analysis

    def end_interview(self) -> dict:
        """End the interview and collect all data."""
        self.state.session.is_active = False
        proctoring_report = self.frame_processor.get_report()
        self.frame_processor.close()

        return {
            "session": self.state.to_dict(),
            "proctoring": proctoring_report.model_dump(),
            "verification_reports": [
                r.model_dump() for r in self.verifier.all_reports
            ],
            "transcript": [
                e.model_dump() for e in self.state.session.transcript
            ],
            "qa_history": [
                qa.model_dump() for qa in self.state.session.qa_history
            ],
        }

    # --- Internal logic ---

    def _decide_and_ask(self) -> str:
        """Use the question strategy to decide and generate the next question."""
        # Check for follow-ups from verifier
        followup = self.verifier.get_next_followup()

        action = self.strategy.pick_next_action(self.state, followup)

        if action["action"] == "end_interview":
            closing = self._generate_question(
                "The interview is ending. Thank the candidate and give a brief positive summary."
            )
            self.state.add_ai_message(closing)
            return closing

        if action["action"] == "transition_phase":
            new_phase = action["new_phase"]
            self.state.set_phase(new_phase)
            is_tech = new_phase in (
                InterviewPhase.TECHNICAL, InterviewPhase.PROJECT_DEEP_DIVE
            )
            self.state.set_technical_question(is_tech)

        if action["action"] == "ask_followup":
            fq: FollowupQuestion = action["question"]
            response = self._generate_question(
                f"Ask this specific follow-up question naturally: {fq.question}\n"
                f"Context: The candidate said '{fq.claim.text}'. "
                f"Probe deeper into this claim."
            )
        else:
            # Normal phase question
            phase = self.state.current_phase
            phase_instruction = PHASE_PROMPTS.get(phase, "Ask the next relevant question.")
            last_answer = self.state.last_user_message

            response = self._generate_question(
                f"Phase: {phase.value}\n"
                f"Instructions: {phase_instruction}\n"
                f"Candidate's last answer: {last_answer}\n"
                f"Questions asked in this phase so far: {self.state.questions_in_phase()}\n"
                f"Briefly acknowledge their previous answer (1 short sentence), then ask "
                f"the next question. Keep it concise — one question only."
            )

        self.state.add_ai_message(response)
        self.state.record_question_asked()
        self.state.start_new_qa(response)  # Start tracking this question's answer
        self.speech_fsm.transition(SpeechEvent.AI_RESPONSE_STARTED)
        return response

    def _generate_question(self, instruction: str) -> str:
        """Send a message to Gemini chat and get a response."""
        if not self._chat:
            return "Could not generate question — chat not initialized."

        try:
            response = self._chat.send_message(instruction)
            return response.text or "Could you tell me more about that?"
        except Exception as e:
            print(f"[Orchestrator] Gemini error: {e}")
            return "That's interesting. Could you elaborate on that?"


    def _build_system_prompt(self) -> str:
        """Build the initial system prompt with resume context."""
        resume = self.state.session.resume_context or ""
        
        # If the resume context is the placeholder from frontend, try to fetch real data
        if "stored in vector DB" in resume or not resume.strip():
            if get_candidate_context and self.state.session.user_id:
                print(f"[Orchestrator] Fetching RAG context for user {self.state.session.user_id}")
                try:
                    chunks = get_candidate_context(self.state.session.user_id, limit=5)
                    if chunks:
                        # Concatenate content from chunks
                        resume = "\n".join([c.get("content", "") for c in chunks])
                    else:
                        resume = "No resume data found in database. Ask generic questions."
                except Exception as e:
                    print(f"[Orchestrator] RAG fetch failed: {e}")
                    resume = "Could not retrieve resume. Proceed with generic interview."
            else:
                resume = "No resume provided."

        # Verify we have something
        if not resume.strip():
             resume = "No resume provided."

        return (
            "You are Zenith — a professional AI interviewer conducting a real job interview. "
            "This is an actual interview that "
            "will determine the candidate's suitability for the role.\n\n"
            "INTERVIEW CONDUCT:\n"
            "- Ask ONE question at a time\n"
            "- Keep questions concise (1-2 sentences)\n"
            "- Sound natural — like a real human interviewer, not a quiz bot\n"
            "- When the candidate mentions a technology choice, ask WHY they chose it\n"
            "- Probe for depth — surface-level answers should trigger follow-ups\n"
            "- Be professional but conversational\n"
            "- Adapt difficulty to the candidate's level\n\n"
            "NATURAL CONVERSATION:\n"
            "- If the candidate says 'hmm', 'let me think', 'uhh', or similar filler words that you believe that the user is thinking, "
            "understand they are thinking and DO NOT treat it as an answer. Wait patiently.\n"
            "- If the candidate asks you to repeat or clarify a question, do so naturally.\n"
            "- If the candidate gives a partial answer and pauses, encourage them to continue "
            "rather than immediately moving on.\n"
            "- Use natural transitions between questions — reference what they just said.\n"
            "- React to their answers briefly before asking the next question "
            "(e.g., 'That's a solid approach.' or 'Interesting choice.').\n\n"
            f"CANDIDATE RESUME:\n{resume}\n\n"
            "Begin the interview."
        )

    def _verify_async(self, text: str, transcript_idx: int):
        """Fire-and-forget verification in background."""
        async def run_and_update():
            report = await self.verifier.run(text)

            # Generate summary feedback
            feedback_lines = []
            for res in report.results:
                feedback_lines.append(f"- {res.verdict.value.title()}: {res.reasoning}")

            if not report.claims:
                 feedback = "No specific technical claims detected."
            else:
                 feedback = "\n".join(feedback_lines)

            # Update state (thread-safe enough for this)
            self.state.update_transcript_entry(
                transcript_idx,
                feedback=feedback,
                verification_data=report.model_dump()
            )

            # Update in-memory Q&A history
            if self.state.session.qa_history:
                last_qa = self.state.session.qa_history[-1]
                last_qa.evaluation = report.model_dump()

                # Save Q&A evaluation to MongoDB concurrently
                if save_qa_evaluation:
                    save_qa_evaluation(
                        self.state.session.session_id,
                        {
                            "question": last_qa.question,
                            "answer": last_qa.answer,
                            "evaluation": last_qa.evaluation,
                            "feedback": feedback,
                            "phase": self.state.current_phase.value,
                        }
                    )

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(run_and_update())
            else:
                loop.run_until_complete(run_and_update())
        except RuntimeError:
             pass
