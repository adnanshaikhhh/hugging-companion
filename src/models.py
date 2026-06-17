# SQLAlchemy ORM models for sessions, subtasks, and reflections.
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


def _new_id() -> str:
    """Generate a short, URL-safe id."""
    return uuid.uuid4().hex[:12]


class SessionRow(Base):
    """A single flow session — one goal, one plan, one timeline."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_min: Mapped[int] = mapped_column(Integer, default=25)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | completed | abandoned
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    share_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    subtasks: Mapped[List["SubtaskRow"]] = relationship(
        "SubtaskRow", back_populates="session", cascade="all, delete-orphan", order_by="SubtaskRow.order"
    )
    reflections: Mapped[List["ReflectionRow"]] = relationship(
        "ReflectionRow", back_populates="session", cascade="all, delete-orphan", order_by="ReflectionRow.created_at"
    )


class SubtaskRow(Base):
    """A single to-do inside a session's plan."""

    __tablename__ = "subtasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("sessions.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    estimate_minutes: Mapped[int] = mapped_column(Integer, default=5)
    order: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    session: Mapped[SessionRow] = relationship("SessionRow", back_populates="subtasks")


class ReflectionRow(Base):
    """A freeform note the user adds during or after a session."""

    __tablename__ = "reflections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("sessions.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[SessionRow] = relationship("SessionRow", back_populates="reflections")