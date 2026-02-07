"""Data models for the answer verification pipeline."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ClaimType(str, Enum):
    TECH_CHOICE = "tech_choice"         # "I used YOLO for detection"
    EXPERIENCE = "experience"           # "I led a team of 5"
    METRIC = "metric"                   # "improved latency by 40%"
    PROJECT = "project"                 # "built a recommendation engine"
    CONCEPT = "concept"                 # "we used microservices architecture"


class Claim(BaseModel):
    text: str
    type: ClaimType
    confidence: float = 1.0             # how confident extraction is
    source_text: str = ""               # original sentence it came from


class VerificationVerdict(str, Enum):
    CONSISTENT = "consistent"           # matches resume
    UNVERIFIABLE = "unverifiable"       # not in resume, can't confirm
    SUSPICIOUS = "suspicious"           # contradicts resume or implausible
    NEEDS_PROBING = "needs_probing"     # surface-level, ask deeper


class VerificationResult(BaseModel):
    claim: Claim
    verdict: VerificationVerdict
    confidence: float
    reasoning: str


class DepthAssessment(BaseModel):
    is_surface_level: bool
    needs_probing: bool
    suggested_angles: List[str] = []    # e.g. ["why not SSD?", "which YOLO version?"]


class FollowupPriority(str, Enum):
    HIGH = "high"       # suspicious or contradictory
    MEDIUM = "medium"   # tech choice needs depth
    LOW = "low"         # just interesting to explore


class FollowupQuestion(BaseModel):
    question: str
    priority: FollowupPriority
    claim: Claim
    context: str = ""


class VerificationReport(BaseModel):
    claims: List[Claim]
    results: List[VerificationResult]
    followups: List[FollowupQuestion]
