"""Async pipeline that orchestrates claim extraction → verification → follow-up generation."""

import asyncio
from typing import List, Optional
from collections import deque

from answer_verifier.config import VerifierConfig
from answer_verifier.core.claim_extractor import ClaimExtractor
from answer_verifier.core.context_retriever import ContextRetriever
from answer_verifier.core.claim_verifier import ClaimVerifier
from answer_verifier.core.knowledge_validator import KnowledgeValidator
from answer_verifier.core.followup_generator import FollowupGenerator
from answer_verifier.models.verification_models import (
    FollowupQuestion,
    VerificationReport,
)


class VerificationPipeline:
    """Runs the full verification pipeline in the background while the interview continues."""

    def __init__(self):
        self.extractor = ClaimExtractor()
        self.retriever = ContextRetriever()
        self.verifier = ClaimVerifier()
        self.validator = KnowledgeValidator()
        self.followup_gen = FollowupGenerator()
        self._followup_queue: deque[FollowupQuestion] = deque(
            maxlen=VerifierConfig.FOLLOWUP_QUEUE_MAX
        )
        self._all_reports: List[VerificationReport] = []

    async def run(self, transcript_chunk: str) -> VerificationReport:
        """Full pipeline: extract → retrieve context → verify → assess depth → generate follow-ups.

        Runs in a thread pool to avoid blocking the event loop (Gemini calls are sync).
        """
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, self._run_sync, transcript_chunk)
        return report

    def _run_sync(self, transcript_chunk: str) -> VerificationReport:
        """Synchronous pipeline execution."""
        # Step 1: Extract claims
        claims = self.extractor.extract(transcript_chunk)
        if not claims:
            return VerificationReport(claims=[], results=[], followups=[])

        # Step 2: Get resume context for all claims
        combined_query = " ".join(c.text for c in claims)
        resume_context = self.retriever.get_context_text(combined_query)

        # Step 3: Verify each claim
        results = self.verifier.verify_batch(claims, resume_context)

        # Step 4: Assess depth for each claim
        depths = [self.validator.assess_depth(c) for c in claims]

        # Step 5: Generate follow-up questions
        followups = self.followup_gen.generate_batch(claims, results, depths)

        # Add to queue
        for fq in followups:
            self._followup_queue.append(fq)

        report = VerificationReport(claims=claims, results=results, followups=followups)
        self._all_reports.append(report)
        return report

    def get_next_followup(self) -> Optional[FollowupQuestion]:
        """Pop the highest-priority follow-up from the queue."""
        if self._followup_queue:
            return self._followup_queue.popleft()
        return None

    def peek_followup(self) -> Optional[FollowupQuestion]:
        """Look at the next follow-up without removing it."""
        if self._followup_queue:
            return self._followup_queue[0]
        return None

    @property
    def followup_count(self) -> int:
        return len(self._followup_queue)

    @property
    def all_reports(self) -> List[VerificationReport]:
        return list(self._all_reports)
