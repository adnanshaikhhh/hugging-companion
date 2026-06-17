# Pydantic schemas — the public contract for the API.
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SubtaskIn(BaseModel):
    """Subtask payload accepted by the AI planner."""
    title: str
    estimate_minutes: int = 5


class SubtaskOut(BaseModel):
    """Subtask as returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    estimate_minutes: int
    order: int
    completed: bool
    completed_at: Optional[datetime] = None


class SessionCreate(BaseModel):
    """Payload for creating a new flow session from a goal string."""
    goal: str = Field(..., min_length=3, max_length=1000, description="What you want to work on.")
    duration_min: Optional[int] = Field(None, ge=5, le=240, description="Focus duration in minutes.")


class SessionUpdate(BaseModel):
    """Payload for updating subtask completion / notes during a session."""
    subtask_id: Optional[str] = None
    subtask_completed: Optional[bool] = None
    note: Optional[str] = None


class SessionSummary(BaseModel):
    """AI-generated summary returned when a session is completed."""
    headline: str
    wins: List[str] = []
    learnings: List[str] = []
    next_steps: List[str] = []
    share_quote: str = ""


class SessionOut(BaseModel):
    """Full session payload as returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    goal: str
    plan: dict
    duration_min: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    summary: Optional[SessionSummary] = None
    share_quote: Optional[str] = None
    subtasks: List[SubtaskOut] = []


class RecallOut(BaseModel):
    """AI recall from past sessions for a given goal."""
    recall: str
    relevant_past: List[SessionOut] = []
    sessions_consulted: int = 0


class StatsOut(BaseModel):
    """Aggregate metrics for the dashboard."""
    total_sessions: int
    total_focus_minutes: int
    completed_sessions: int
    completion_rate: float
    avg_session_minutes: float
    current_streak_days: int
    longest_streak_days: int
    most_productive_hour: Optional[int] = None
    by_day: List[dict] = []


class HealthOut(BaseModel):
    """Health check response."""
    status: str
    app: str
    ai_mode: str  # "openai" | "mock"