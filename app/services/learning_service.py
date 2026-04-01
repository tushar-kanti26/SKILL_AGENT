from datetime import datetime

from sqlalchemy.orm import Session

from app.agent.graph import learning_agent
from app.db.models import ChatMessage, Learner, LearningPlan, LearningTask
from app.services.planner import build_skill_tree_and_schedule


def get_or_create_learner(db: Session, learner_name: str) -> Learner:
    learner = db.query(Learner).filter(Learner.name == learner_name).first()
    if learner:
        return learner

    learner = Learner(name=learner_name)
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


def process_chat(db: Session, learner: Learner, message: str, profile_updates: dict | None = None) -> dict:
    profile_updates = profile_updates or {}

    state = {
        "user_message": message,
        "profile": {
            "target_skill": profile_updates.get("target_skill", learner.target_skill),
            "current_level": profile_updates.get("current_level", learner.current_level),
            "weekly_hours": profile_updates.get("weekly_hours", learner.weekly_hours),
            "timeline_weeks": profile_updates.get("timeline_weeks", learner.timeline_weeks),
            "goal": profile_updates.get("goal", learner.goal),
        },
        "assistant_message": "",
        "ready_for_plan": False,
    }

    result = learning_agent.invoke(state)
    profile = result["profile"]

    learner.target_skill = profile.get("target_skill")
    learner.current_level = profile.get("current_level")
    learner.weekly_hours = profile.get("weekly_hours")
    learner.timeline_weeks = profile.get("timeline_weeks")
    learner.goal = profile.get("goal")

    db.add(ChatMessage(learner_id=learner.id, role="user", content=message))
    db.add(
        ChatMessage(
            learner_id=learner.id,
            role="assistant",
            content=result["assistant_message"],
        )
    )
    db.commit()
    db.refresh(learner)

    return {
        "learner_id": learner.id,
        "assistant_message": result["assistant_message"],
        "collected_profile": profile,
        "ready_for_plan": result["ready_for_plan"],
    }


def generate_plan(db: Session, learner: Learner) -> LearningPlan:
    missing = []
    for field in ["target_skill", "current_level", "weekly_hours", "timeline_weeks", "goal"]:
        if not getattr(learner, field):
            missing.append(field)

    if missing:
        raise ValueError(f"Missing profile fields before plan generation: {missing}")

    profile = {
        "target_skill": learner.target_skill,
        "current_level": learner.current_level,
        "weekly_hours": learner.weekly_hours,
        "timeline_weeks": learner.timeline_weeks,
        "goal": learner.goal,
    }

    generated = build_skill_tree_and_schedule(profile)

    plan = LearningPlan(
        learner_id=learner.id,
        skill_name=learner.target_skill,
        level=learner.current_level,
        goal=learner.goal,
        hours_per_week=learner.weekly_hours,
        timeline_weeks=learner.timeline_weeks,
        skill_tree=generated["skill_tree"],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    for task in generated["tasks"]:
        db_task = LearningTask(plan_id=plan.id, **task)
        db.add(db_task)

    db.commit()
    db.refresh(plan)
    return plan


def list_tasks(db: Session, plan_id: int):
    return (
        db.query(LearningTask)
        .filter(LearningTask.plan_id == plan_id)
        .order_by(LearningTask.week_number, LearningTask.day_label)
        .all()
    )


def update_task_progress(db: Session, task: LearningTask, completed: bool) -> LearningTask:
    task.completed = completed
    task.completed_at = datetime.utcnow() if completed else None
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def progress_summary(db: Session, learner_id: int, plan_id: int) -> dict:
    tasks = (
        db.query(LearningTask)
        .join(LearningPlan, LearningTask.plan_id == LearningPlan.id)
        .filter(LearningPlan.id == plan_id, LearningPlan.learner_id == learner_id)
        .all()
    )

    total = len(tasks)
    completed = len([task for task in tasks if task.completed])
    rate = round((completed / total) * 100, 2) if total else 0.0

    return {
        "learner_id": learner_id,
        "plan_id": plan_id,
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate": rate,
    }
