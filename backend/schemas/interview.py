from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class InterviewStartRequest(BaseModel):
    role: str
    difficulty: str
    num_questions: int = Field(default=5, ge=5, le=10)


class InterviewStartResponse(BaseModel):
    interview_id: int
    role: str
    difficulty: str
    questions: list[str]
    attempt_number: int
    created_at: datetime
    duration_seconds: int


class InterviewSubmitRequest(BaseModel):
    interview_id: int
    answers: list[str]


class InterviewResultResponse(BaseModel):
    interview_id: int
    role: str
    difficulty: str
    scores: dict[str, Any]
    feedback: dict[str, Any]
    created_at: datetime


class InterviewHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    difficulty: str
    attempt_number: int
    questions: list[str]
    answers: list[str]
    scores: Optional[Dict[str, Any]]
    feedback: Optional[Dict[str, Any]]
    created_at: datetime
    status: str


class BreakdownItem(BaseModel):
    label: str
    count: int
    average_score: float


class ProgressPoint(BaseModel):
    label: str
    role: str
    score: float
    max_score: int


class RecentFeedbackItem(BaseModel):
    interview_id: int
    role: str
    difficulty: str
    summary: str
    score: float
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float
    best_score: float
    completion_rate: float
    role_breakdown: list[BreakdownItem]
    difficulty_breakdown: list[BreakdownItem]
    progress_series: list[ProgressPoint]
    recent_feedback: list[RecentFeedbackItem]
