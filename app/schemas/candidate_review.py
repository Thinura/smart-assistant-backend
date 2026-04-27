from typing import Literal

from pydantic import BaseModel, Field


class CandidateReviewResult(BaseModel):
    summary: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    strengths: list[str]
    risks: list[str]
    interview_focus_areas: list[str]
    recommendation: Literal["shortlist", "hold", "reject"]
    confidence: Literal["low", "medium", "high"]
