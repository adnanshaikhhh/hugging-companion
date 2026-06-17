# Insights endpoints — aggregate stats for the dashboard.
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import SessionRow
from src.schemas import StatsOut

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)) -> StatsOut:
    """Compute aggregate metrics across every stored session."""
    rows: List[SessionRow] = db.query(SessionRow).order_by(SessionRow.started_at.asc()).all()
    if not rows:
        return StatsOut(
            total_sessions=0,
            total_focus_minutes=0,
            completed_sessions=0,
            completion_rate=0.0,
            avg_session_minutes=0.0,
            current_streak_days=0,
            longest_streak_days=0,
            most_productive_hour=None,
            by_day=[],
        )

    completed = [r for r in rows if r.status == "completed"]
    total_minutes = sum((r.ended_at - r.started_at).total_seconds() / 60.0 for r in completed if r.ended_at)
    # If a session has no ended_at (active), use the planned duration as a soft estimate.
    estimated_minutes = total_minutes + sum(r.duration_min for r in rows if r.status == "active")
    avg = (total_minutes / len(completed)) if completed else 0.0

    # Streaks based on day-of-completion.
    day_keys = sorted({(r.ended_at or r.started_at).date().isoformat() for r in rows if r.ended_at or r.status == "completed"})
    longest = 0
    current = 0
    prev = None
    for k in day_keys:
        d = datetime.fromisoformat(k).date()
        if prev is None or d == prev + timedelta(days=1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        prev = d

    # Current streak is only valid if the most-recent day is today or yesterday.
    if day_keys:
        last_day = datetime.fromisoformat(day_keys[-1]).date()
        if (datetime.utcnow().date() - last_day).days > 1:
            current = 0

    # Most productive hour — when most sessions started.
    hours = Counter((r.started_at.hour for r in rows))
    most_productive_hour = hours.most_common(1)[0][0] if hours else None

    # Last 14 days, by day, for the chart.
    by_day_map: Counter = Counter()
    for r in rows:
        d = r.started_at.date().isoformat()
        by_day_map[d] += 1
    today = datetime.utcnow().date()
    by_day: List[dict] = []
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        by_day.append({"date": d, "count": by_day_map.get(d, 0)})

    completion_rate = (len(completed) / len(rows)) if rows else 0.0

    return StatsOut(
        total_sessions=len(rows),
        total_focus_minutes=int(estimated_minutes),
        completed_sessions=len(completed),
        completion_rate=round(completion_rate, 3),
        avg_session_minutes=round(avg, 1),
        current_streak_days=current,
        longest_streak_days=longest,
        most_productive_hour=most_productive_hour,
        by_day=by_day,
    )