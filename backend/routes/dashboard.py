from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.interview import Interview
from backend.models.user import User
from backend.schemas.interview import DashboardStatsResponse
from backend.services.auth_service import get_current_user


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    completed_interviews = [interview for interview in interviews if interview.scores]
    average_scores = [float(interview.scores.get("average", 0)) for interview in completed_interviews]

    role_buckets: dict[str, list[float]] = defaultdict(list)
    difficulty_buckets: dict[str, list[float]] = defaultdict(list)
    recent_feedback = []
    progress_series = []

    for interview in completed_interviews:
        total_score = float(interview.scores.get("total", 0))
        average_score = float(interview.scores.get("average", 0))
        role_buckets[interview.role].append(average_score)
        difficulty_buckets[interview.difficulty].append(average_score)
        if len(progress_series) < 8:
            progress_series.append(
                {
                    "label": interview.created_at.strftime("%d %b"),
                    "role": interview.role,
                    "score": total_score,
                    "max_score": int(interview.scores.get("max_total", 0)),
                }
            )
        if len(recent_feedback) < 5:
            recent_feedback.append(
                {
                    "interview_id": interview.id,
                    "role": interview.role,
                    "difficulty": interview.difficulty,
                    "summary": interview.feedback.get("summary", "Review completed."),
                    "score": total_score,
                    "created_at": interview.created_at,
                }
            )

    role_breakdown = [
        {
            "label": label,
            "count": len(scores),
            "average_score": round(sum(scores) / len(scores), 2),
        }
        for label, scores in sorted(role_buckets.items())
    ]
    difficulty_breakdown = [
        {
            "label": label,
            "count": len(scores),
            "average_score": round(sum(scores) / len(scores), 2),
        }
        for label, scores in sorted(difficulty_buckets.items())
    ]

    completed_count = len(completed_interviews)
    total_count = len(interviews)

    return DashboardStatsResponse(
        total_interviews=total_count,
        completed_interviews=completed_count,
        average_score=round(sum(average_scores) / completed_count, 2) if completed_count else 0.0,
        best_score=max(average_scores) if average_scores else 0.0,
        completion_rate=round((completed_count / total_count) * 100, 2) if total_count else 0.0,
        role_breakdown=role_breakdown,
        difficulty_breakdown=difficulty_breakdown,
        progress_series=list(reversed(progress_series)),
        recent_feedback=recent_feedback,
    )
