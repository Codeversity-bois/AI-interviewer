"""Extract verifiable claims from user speech using Gemini."""

import os
import json
from typing import List

from google import genai
from google.genai import types
from dotenv import load_dotenv

from answer_verifier.config import VerifierConfig
from answer_verifier.models.verification_models import Claim, ClaimType

load_dotenv(dotenv_path="interview_manager/.env")


EXTRACTION_PROMPT = """Analyze the following interview response and extract verifiable claims.

For each claim, identify:
- text: the exact claim made
- type: one of [tech_choice, experience, metric, project, concept]
- source_text: the original sentence

Types explained:
- tech_choice: specific technology/tool/framework chosen (e.g. "used YOLO", "built with React")
- experience: experience claims (e.g. "led a team of 5", "3 years of Python")
- metric: quantified results (e.g. "improved latency by 40%", "processed 1M requests")
- project: project descriptions (e.g. "built a recommendation engine")
- concept: architectural/design claims (e.g. "used microservices", "implemented CI/CD")

Return ONLY valid JSON array. Max {max_claims} claims. Focus on the most important/verifiable ones.

Response text:
\"\"\"{text}\"\"\"

Return format:
[{{"text": "...", "type": "...", "source_text": "..."}}]
"""


class ClaimExtractor:
    """Extracts structured claims from interview responses."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)

    def extract(self, transcript_chunk: str) -> List[Claim]:
        """Parse a user's speech into structured claims."""
        if not transcript_chunk or len(transcript_chunk.strip()) < 20:
            return []

        prompt = EXTRACTION_PROMPT.format(
            text=transcript_chunk,
            max_claims=VerifierConfig.MAX_CLAIMS_PER_RESPONSE,
        )

        try:
            response = self._client.models.generate_content(
                model=VerifierConfig.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=VerifierConfig.VERIFICATION_TEMPERATURE,
                    max_output_tokens=1024,
                ),
            )

            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0]

            claims_data = json.loads(raw)
            claims = []
            for item in claims_data[:VerifierConfig.MAX_CLAIMS_PER_RESPONSE]:
                claims.append(Claim(
                    text=item["text"],
                    type=ClaimType(item["type"]),
                    source_text=item.get("source_text", ""),
                ))
            return claims

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[ClaimExtractor] Parse error: {e}")
            return []
        except Exception as e:
            print(f"[ClaimExtractor] API error: {e}")
            return []
