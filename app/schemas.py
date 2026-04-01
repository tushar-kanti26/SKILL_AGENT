from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    learner_name: str = Field(min_length=2, max_length=120)
    message: str = Field(min_length=1)
    target_skill: str | None = None
    current_level: str | None = None
    weekly_hours: int | None = None
    timeline_weeks: int | None = None
    goal: str | None = None


class ChatResponse(BaseModel):
    learner_id: int
    assistant_message: str
    collected_profile: dict
    ready_for_plan: bool


class PlanCreateRequest(BaseModel):
    learner_id: int


class PlanResponse(BaseModel):
    plan_id: int
    learner_id: int
    skill_name: str
    level: str
    goal: str
    hours_per_week: int
    timeline_weeks: int
    skill_tree: dict


class TaskResponse(BaseModel):
    task_id: int
    week_number: int
    day_label: str
    title: str
    resource_type: str
    resource_title: str
    resource_url: str
    estimated_minutes: int
    completed: bool


class ProgressUpdateRequest(BaseModel):
    completed: bool


class ProgressSummaryResponse(BaseModel):
    learner_id: int
    plan_id: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float


class TaskProgressResponse(BaseModel):
    task_id: int
    completed: bool
    completed_at: datetime | None


ResourceType = Literal["youtube", "website", "book"]
