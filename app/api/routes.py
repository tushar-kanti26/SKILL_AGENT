from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Learner, LearningPlan, LearningTask
from app.schemas import (
    ChatRequest,
    ChatResponse,
    PlanCreateRequest,
    PlanResponse,
    ProgressSummaryResponse,
    ProgressUpdateRequest,
    TaskProgressResponse,
    TaskResponse,
)
from app.services.learning_service import (
    generate_plan,
    get_or_create_learner,
    list_tasks,
    process_chat,
    progress_summary,
    update_task_progress,
)

router = APIRouter(prefix="/api", tags=["skill-agent"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    learner = get_or_create_learner(db, payload.learner_name)
    response = process_chat(
        db,
        learner,
        payload.message,
        {
            "target_skill": payload.target_skill,
            "current_level": payload.current_level,
            "weekly_hours": payload.weekly_hours,
            "timeline_weeks": payload.timeline_weeks,
            "goal": payload.goal,
        },
    )
    return response


@router.post("/plans", response_model=PlanResponse)
def create_plan(payload: PlanCreateRequest, db: Session = Depends(get_db)):
    learner = db.query(Learner).filter(Learner.id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    try:
        plan = generate_plan(db, learner)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "plan_id": plan.id,
        "learner_id": plan.learner_id,
        "skill_name": plan.skill_name,
        "level": plan.level,
        "goal": plan.goal,
        "hours_per_week": plan.hours_per_week,
        "timeline_weeks": plan.timeline_weeks,
        "skill_tree": plan.skill_tree,
    }


@router.get("/plans/{plan_id}/tasks", response_model=list[TaskResponse])
def get_plan_tasks(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    tasks = list_tasks(db, plan_id)
    return [
        {
            "task_id": task.id,
            "week_number": task.week_number,
            "day_label": task.day_label,
            "title": task.title,
            "resource_type": task.resource_type,
            "resource_title": task.resource_title,
            "resource_url": task.resource_url,
            "estimated_minutes": task.estimated_minutes,
            "completed": task.completed,
        }
        for task in tasks
    ]


@router.patch("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
def set_task_progress(task_id: int, payload: ProgressUpdateRequest, db: Session = Depends(get_db)):
    task = db.query(LearningTask).filter(LearningTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated = update_task_progress(db, task, payload.completed)
    return {
        "task_id": updated.id,
        "completed": updated.completed,
        "completed_at": updated.completed_at,
    }


@router.get("/learners/{learner_id}/plans/{plan_id}/progress", response_model=ProgressSummaryResponse)
def get_progress(learner_id: int, plan_id: int, db: Session = Depends(get_db)):
    plan = (
        db.query(LearningPlan)
        .filter(LearningPlan.id == plan_id, LearningPlan.learner_id == learner_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found for learner")

    return progress_summary(db, learner_id, plan_id)
