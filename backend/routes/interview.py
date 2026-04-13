from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.interview import Interview
from backend.models.user import User
from backend.schemas.interview import (
    InterviewHistoryItem,
    InterviewResultResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewSubmitRequest,
)
from backend.services.ai_service import evaluate_interview
from backend.services.auth_service import get_current_user
from backend.services.question_service import (
    generate_questions,
    get_interview_duration,
    normalize_difficulty,
    normalize_role,
)


router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        role = normalize_role(payload.role)
        difficulty = normalize_difficulty(payload.difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    questions = generate_questions(role, difficulty, payload.num_questions)
    attempt_number = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id, Interview.role == role, Interview.difficulty == difficulty)
        .count()
        + 1
    )

    interview = Interview(
        user_id=current_user.id,
        role=role,
        difficulty=difficulty,
        questions=questions,
        answers=[],
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return InterviewStartResponse(
        interview_id=interview.id,
        role=role,
        difficulty=difficulty,
        questions=questions,
        attempt_number=attempt_number,
        created_at=interview.created_at,
        duration_seconds=get_interview_duration(len(questions)),
    )


@router.post("/submit", response_model=InterviewResultResponse)
def submit_interview(
    payload: InterviewSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = (
        db.query(Interview)
        .filter(Interview.id == payload.interview_id, Interview.user_id == current_user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if interview.scores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This interview has already been submitted. Start a new attempt to retry.",
        )

    if len(payload.answers) != len(interview.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(interview.questions)} answers, received {len(payload.answers)}.",
        )

    evaluation = evaluate_interview(interview.role, interview.difficulty, interview.questions, payload.answers)
    interview.answers = payload.answers
    interview.scores = evaluation["scores"]
    interview.feedback = evaluation["feedback"]

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return InterviewResultResponse(
        interview_id=interview.id,
        role=interview.role,
        difficulty=interview.difficulty,
        scores=interview.scores,
        feedback=interview.feedback,
        created_at=interview.created_at,
    )


@router.get("/history", response_model=list[InterviewHistoryItem])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.asc())
        .all()
    )

    attempt_counters: dict[tuple[str, str], int] = {}
    history_items: list[InterviewHistoryItem] = []

    for interview in interviews:
        counter_key = (interview.role, interview.difficulty)
        attempt_counters[counter_key] = attempt_counters.get(counter_key, 0) + 1
        history_items.append(
            InterviewHistoryItem(
                id=interview.id,
                role=interview.role,
                difficulty=interview.difficulty,
                attempt_number=attempt_counters[counter_key],
                questions=interview.questions or [],
                answers=interview.answers or [],
                scores=interview.scores,
                feedback=interview.feedback,
                created_at=interview.created_at,
                status="completed" if interview.scores else "in_progress",
            )
        )

    return list(reversed(history_items))
