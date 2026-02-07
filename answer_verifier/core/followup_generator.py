"""Generate targeted follow-up questions from verification results."""

from typing import List, Optional

from answer_verifier.models.verification_models import (
    Claim,
    ClaimType,
    VerificationResult,
    VerificationVerdict,
    DepthAssessment,
    FollowupQuestion,
    FollowupPriority,
)


class FollowupGenerator:
    """Produces follow-up questions based on claim verification and depth assessment."""

    def generate(
        self,
        claim: Claim,
        verification: VerificationResult,
        depth: DepthAssessment,
    ) -> Optional[FollowupQuestion]:
        """Generate a follow-up question for a single claim. Returns None if no follow-up needed."""

        # Suspicious claims get high priority probing
        if verification.verdict == VerificationVerdict.SUSPICIOUS:
            return FollowupQuestion(
                question=self._build_suspicious_question(claim, verification),
                priority=FollowupPriority.HIGH,
                claim=claim,
                context=verification.reasoning,
            )

        # Tech choices that need depth probing
        if depth.needs_probing and depth.suggested_angles:
            priority = FollowupPriority.MEDIUM
            if claim.type == ClaimType.TECH_CHOICE:
                priority = FollowupPriority.HIGH  # tech choices are always interesting

            return FollowupQuestion(
                question=self._build_probe_question(claim, depth.suggested_angles),
                priority=priority,
                claim=claim,
                context=f"Angles: {', '.join(depth.suggested_angles)}",
            )

        # Unverifiable claims with low confidence
        if verification.verdict == VerificationVerdict.UNVERIFIABLE:
            if verification.confidence < 0.5:
                return FollowupQuestion(
                    question=self._build_clarification_question(claim),
                    priority=FollowupPriority.LOW,
                    claim=claim,
                    context="Claim not found in resume",
                )

        return None

    def generate_batch(
        self,
        claims: List[Claim],
        verifications: List[VerificationResult],
        depths: List[DepthAssessment],
    ) -> List[FollowupQuestion]:
        """Generate follow-ups for multiple claims."""
        followups = []
        for claim, ver, dep in zip(claims, verifications, depths):
            q = self.generate(claim, ver, dep)
            if q:
                followups.append(q)
        # Sort by priority: HIGH first
        priority_order = {FollowupPriority.HIGH: 0, FollowupPriority.MEDIUM: 1, FollowupPriority.LOW: 2}
        followups.sort(key=lambda f: priority_order[f.priority])
        return followups

    # --- question builders ---

    def _build_suspicious_question(self, claim: Claim, verification: VerificationResult) -> str:
        return (
            f"You mentioned {claim.text}. "
            f"Can you walk me through that in more detail? "
            f"Specifically, what was your exact role and contribution there?"
        )

    def _build_probe_question(self, claim: Claim, angles: List[str]) -> str:
        # Use the first suggested angle as the primary question
        angle = angles[0]
        return (
            f"That's interesting — you mentioned {claim.text}. {angle}"
        )

    def _build_clarification_question(self, claim: Claim) -> str:
        return (
            f"I noticed you mentioned {claim.text}. "
            f"Could you tell me more about the context around that?"
        )
