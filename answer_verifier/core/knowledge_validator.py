"""Assess depth of technical claims and suggest probing angles."""

import os
import json
from typing import List

from google import genai
from google.genai import types
from dotenv import load_dotenv

from answer_verifier.config import VerifierConfig
from answer_verifier.models.verification_models import Claim, ClaimType, DepthAssessment

load_dotenv(dotenv_path="interview_manager/.env")

DEPTH_PROMPT = """A candidate in a tech interview said: "{claim_text}"

This is a {claim_type} type claim.

Assess:
1. Is this a surface-level statement that any beginner could say, or does it show depth?
2. What follow-up angles would test if they really understand this?
3. What are the common alternatives they should be able to compare against?

Return ONLY valid JSON:
{{
  "is_surface_level": true/false,
  "needs_probing": true/false,
  "suggested_angles": ["angle 1", "angle 2", "angle 3"]
}}

Keep suggested_angles to 2-3 items max. Make them specific and technical.
For example, if they said "I used YOLO":
- "Why YOLO over SSD or Faster R-CNN for your use case?"
- "Which YOLO version and what was your mAP?"
- "How did you handle the speed-accuracy tradeoff?"
"""


class KnowledgeValidator:
    """Determines if a claim is surface-level and suggests probing questions."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)

    def assess_depth(self, claim: Claim) -> DepthAssessment:
        """Assess whether a claim needs deeper probing."""
        # Only probe tech choices, concepts, and metrics — not basic experience
        if claim.type == ClaimType.EXPERIENCE:
            return DepthAssessment(
                is_surface_level=False,
                needs_probing=False,
                suggested_angles=[],
            )

        prompt = DEPTH_PROMPT.format(
            claim_text=claim.text,
            claim_type=claim.type.value,
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
            return DepthAssessment(
                is_surface_level=data.get("is_surface_level", True),
                needs_probing=data.get("needs_probing", True),
                suggested_angles=data.get("suggested_angles", [])[:3],
            )

        except Exception as e:
            print(f"[KnowledgeValidator] Error: {e}")
            return DepthAssessment(
                is_surface_level=True,
                needs_probing=True,
                suggested_angles=["Can you elaborate on that?"],
            )
