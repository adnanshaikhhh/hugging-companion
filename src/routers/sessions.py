# Session endpoints — create, list, update, complete, delete.
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.ai.companion import Companion
from src.database import get_db
from src.models import ReflectionRow, SessionRow, SubtaskRow
from src.schemas import SessionCreate, SessionOut, SessionUpdate

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_companion: Companion | None = None


def get_companion() -> Companion:
    """FastAPI dependency — single Companion instance per process."""
    global _companion
    if _companion is None:
        _companion = Companion()
    return _companion


def _title_from_goal(goal: str) -> str:
    """Best-effort short title for display / sharing."""
    words = goal.strip().split()
    return " ".join(words[:6]).title() or "Flow Session"


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    companion: Companion = Depends(get_companion),
) -> SessionOut:
    """Create a new flow session and generate an AI plan for the goal."""
    from src.config import get_settings
    settings = get_settings()
    duration = payload.duration_min or settings.default_duration_min

    plan = companion.generate_plan(payload.goal, duration)

    row = SessionRow(
        title=plan.get("title") or _title_from_goal(payload.goal),
        goal=payload.goal,
        plan={
            "plan_intro": plan.get("plan_intro", ""),
            "energy_advice": plan.get("energy_advice", ""),
        },
        duration_min=duration,
        status="active",
    )
    db.add(row)
    db.flush()  # populate row.id

    for i, s in enumerate(plan.get("subtasks", [])):
        db.add(
            SubtaskRow(
                session_id=row.id,
                title=s["title"],
                estimate_minutes=int(s.get("estimate_minutes", 5)),
                order=i,
            )
        )

    db.commit()
    db.refresh(row)
    return SessionOut.model_validate(row)


@router.get("", response_model=List[SessionOut])
def list_sessions(limit: int = 50, db: Session = Depends(get_db)) -> List[SessionOut]:
    """List sessions, newest first."""
    rows = db.query(SessionRow).order_by(SessionRow.started_at.desc()).limit(min(limit, 200)).all()
    return [SessionOut.model_validate(r) for r in rows]


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionOut:
    """Get a single session by id."""
    row = db.get(SessionRow, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut.model_validate(row)


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
) -> SessionOut:
    """Toggle a subtask complete, or append a freeform note."""
    row = db.get(SessionRow, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    if payload.subtask_id is not None:
        sub = db.get(SubtaskRow, payload.subtask_id)
        if not sub or sub.session_id != session_id:
            raise HTTPException(status_code=404, detail="Subtask not found")
        if payload.subtask_completed is not None:
            sub.completed = bool(payload.subtask_completed)
            sub.completed_at = datetime.utcnow() if sub.completed else None

    if payload.note:
        db.add(ReflectionRow(session_id=session_id, content=payload.note))

    db.commit()
    db.refresh(row)
    return SessionOut.model_validate(row)


@router.post("/{session_id}/complete", response_model=SessionOut)
def complete_session(
    session_id: str,
    db: Session = Depends(get_db),
    companion: Companion = Depends(get_companion),
) -> SessionOut:
    """Mark a session as complete and generate an AI summary."""
    row = db.get(SessionRow, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.status == "completed":
        return SessionOut.model_validate(row)

    completed_titles = [s.title for s in row.subtasks if s.completed]
    skipped_titles = [s.title for s in row.subtasks if not s.completed]
    notes = "\n".join(r.content for r in row.reflections)

    summary = companion.generate_summary(
        goal=row.goal,
        title=row.title,
        duration=row.duration_min,
        completed=completed_titles,
        skipped=skipped_titles,
        notes=notes,
    )
    row.summary = summary
    row.share_quote = summary.get("share_quote")
    row.ended_at = datetime.utcnow()
    row.status = "completed"
    db.commit()
    db.refresh(row)
    return SessionOut.model_validate(row)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a session and all of its subtasks/reflections."""
    row = db.get(SessionRow, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(row)
    db.commit()
    return None