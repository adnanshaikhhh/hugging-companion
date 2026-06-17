# Memory endpoints — AI recall from past sessions.
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.ai.companion import Companion
from src.database import get_db
from src.models import SessionRow
from src.schemas import RecallOut, SessionOut
from src.routers.sessions import get_companion

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/recall", response_model=RecallOut)
def recall(
    goal: str = Query(..., min_length=3, max_length=500),
    db: Session = Depends(get_db),
    companion: Companion = Depends(get_companion),
) -> RecallOut:
    """Return an AI-generated recall for a goal, grounded in past sessions."""
    data = companion.generate_recall(goal)
    ids = data.get("ids", [])
    rows: List[SessionRow] = []
    if ids:
        rows = db.query(SessionRow).filter(SessionRow.id.in_(ids)).all()
        # Preserve the AI's ordering.
        order = {sid: i for i, sid in enumerate(ids)}
        rows.sort(key=lambda r: order.get(r.id, 999))
    return RecallOut(
        recall=data.get("recall", ""),
        relevant_past=[SessionOut.model_validate(r) for r in rows],
        sessions_consulted=len(rows),
    )