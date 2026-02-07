"""Verify claims against resume context and technical plausibility."""

import os
import json
from typing import List

from google import genai
from google.genai import types
from dotenv import load_dotenv

from answer_verifier.config import VerifierConfig
from answer_verifier.models.verification_models import (
    Claim,
    VerificationResult,
    VerificationVerdict,
)

load_dotenv(dotenv_path="interview_manager/.env")

VERIFY_PROMPT = """You are verifying an interview candidate's claim against their resume.

Claim: "{claim_text}"
Claim type: {claim_type}

Resume context:
{resume_context}

Evaluate:
1. Does the resume support this claim? (consistent / unverifiable / suspicious)
2. Is the claim technically plausible? (e.g. using YOLO for NLP would be suspicious)
3. How confident are you in your verdict? (0.0 to 1.0)

Return ONLY valid JSON:
{{"verdict": "consistent|unverifiable|suspicious|needs_probing", "confidence": 0.8, "reasoning": "..."}}
"""


class ClaimVerifier:
    """Cross-checks claims against resume and technical knowledge."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)

    def verify(self, claim: Claim, resume_context: str) -> VerificationResult:
        """Verify a single claim against resume context."""
        prompt = VERIFY_PROMPT.format(
            claim_text=claim.text,
            claim_type=claim.type.value,
            resume_context=resume_context or "No resume context available.",
        )

        try:
            response = self._client.models.generate_content(
                model=VerifierConfig.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=VerifierConfig.VERIFICATION_TEMPERATURE,
                    max_output_tokens=512,
                ),
            )

            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0]

            data = json.loads(raw)
            return VerificationResult(
                claim=claim,
                verdict=VerificationVerdict(data["verdict"]),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
            )

        except Exception as e:
            print(f"[ClaimVerifier] Error: {e}")
            return VerificationResult(
                claim=claim,
                verdict=VerificationVerdict.UNVERIFIABLE,
                confidence=0.0,
                reasoning=f"Verification failed: {e}",
            )

    def verify_batch(self, claims: List[Claim], resume_context: str) -> List[VerificationResult]:
        """Verify multiple claims sequentially."""
        return [self.verify(claim, resume_context) for claim in claims]
