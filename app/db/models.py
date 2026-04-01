from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_skill: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weekly_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeline_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plans = relationship("LearningPlan", back_populates="learner", cascade="all, delete")
    messages = relationship("ChatMessage", back_populates="learner", cascade="all, delete")


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    timeline_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_tree: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="plans")
    tasks = relationship("LearningTask", back_populates="plan", cascade="all, delete")


class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("learning_plans.id"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_label: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_title: Mapped[str] = mapped_column(String(250), nullable=False)
    resource_url: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    plan = relationship("LearningPlan", back_populates="tasks")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="messages")
