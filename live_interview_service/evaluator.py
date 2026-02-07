"""Parallel interview evaluator — runs alongside the live Gemini session.

Uses a separate Gemini text model to evaluate each candidate turn as it happens.
Accumulates evaluations into a structured JSON that can be retrieved at any time.
"""

import json
import asyncio
from typing import Optional

from google import genai
from google.genai import types

from live_interview_service.config import GEMINI_API_KEY, EVAL_MODEL
from live_interview_service.models import (
    InterviewEvaluation, TurnEvaluation, TranscriptTurn,
)
from live_interview_service.prompts import (
    EVALUATION_PROMPT, SUMMARY_EVALUATION_PROMPT,
)


class LiveEvaluator:
    """Evaluates interview turns in parallel using Gemini text model."""

    def __init__(self, session_id: str, candidate_id: str, job_id: str, job_description: str):
        self.job_description = job_description
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._transcript: list[TranscriptTurn] = []
        self._turn_number = 0

        self.evaluation = InterviewEvaluation(
            candidate_id=candidate_id,
            job_id=job_id,
            session_id=session_id,
        )

    def add_turn(self, role: str, text: str):
        """Record a transcript turn (called from the main session loop)."""
        self._transcript.append(TranscriptTurn(role=role, text=text))

    async def evaluate_turn(self, question: str, answer: str):
        """Evaluate a single candidate response. Runs in background without blocking audio."""
        self._turn_number += 1
        turn_num = self._turn_number

        try:
            transcript_text = self._format_transcript()
            prompt = EVALUATION_PROMPT.format(
                job_description=self.job_description,
                transcript=transcript_text,
                question=question,
                answer=answer,
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=EVAL_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3),
                ),
            )

            raw = response.text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            scores = json.loads(raw)

            turn_eval = TurnEvaluation(
                turn_number=turn_num,
                question_asked=question,
                candidate_response=answer,
                relevance_score=scores.get("relevance_score", 0),
                depth_score=scores.get("depth_score", 0),
                communication_score=scores.get("communication_score", 0),
                technical_accuracy=scores.get("technical_accuracy", 0),
                key_observations=scores.get("key_observations", []),
                red_flags=scores.get("red_flags", []),
                follow_up_needed=scores.get("follow_up_needed", False),
                follow_up_reason=scores.get("follow_up_reason", ""),
            )

            self.evaluation.turns.append(turn_eval)
            self._update_running_averages()

        except Exception as e:
            print(f"[Evaluator] Turn {turn_num} evaluation failed: {e}")
            # Still record the turn with zero scores so we don't lose track
            self.evaluation.turns.append(TurnEvaluation(
                turn_number=turn_num,
                question_asked=question,
                candidate_response=answer,
            ))

    async def finalize(self) -> InterviewEvaluation:
        """Generate the final summary evaluation after the interview ends."""
        try:
            transcript_text = self._format_transcript()
            turn_scores = json.dumps(
                [t.model_dump() for t in self.evaluation.turns], indent=2
            )

            prompt = SUMMARY_EVALUATION_PROMPT.format(
                job_description=self.job_description,
                transcript=transcript_text,
                turn_scores=turn_scores,
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=EVAL_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3),
                ),
            )

            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            summary = json.loads(raw)
            print(summary)
            self.evaluation.overall_score = summary.get("overall_score", 0)
            self.evaluation.technical_competency = summary.get("technical_competency", 0)
            self.evaluation.communication_skills = summary.get("communication_skills", 0)
            self.evaluation.problem_solving = summary.get("problem_solving", 0)
            self.evaluation.cultural_fit = summary.get("cultural_fit", 0)
            self.evaluation.strengths = summary.get("strengths", [])
            self.evaluation.weaknesses = summary.get("weaknesses", [])
            self.evaluation.recommendation = summary.get("recommendation", "")

        except Exception as e:
            print(f"[Evaluator] Final evaluation failed: {e}")

        return self.evaluation

    def get_evaluation_snapshot(self) -> dict:
        """Return the current evaluation state as a dict (for real-time access)."""
        import time
        self.evaluation.updated_at = time.time()
        return self.evaluation.model_dump()

    def _format_transcript(self) -> str:
        lines = []
        for t in self._transcript:
            label = "Interviewer" if t.role == "interviewer" else "Candidate"
            lines.append(f"{label}: {t.text}")
        return "\n".join(lines)

    def _update_running_averages(self):
        """Recompute running average scores from all turns."""
        turns = self.evaluation.turns
        if not turns:
            return
        n = len(turns)
        self.evaluation.overall_score = round(
            sum(
                (t.relevance_score + t.depth_score + t.communication_score + t.technical_accuracy) / 4
                for t in turns
            ) / n, 2
        )
        self.evaluation.technical_competency = round(
            sum(t.technical_accuracy for t in turns) / n, 2
        )
        self.evaluation.communication_skills = round(
            sum(t.communication_score for t in turns) / n, 2
        )
