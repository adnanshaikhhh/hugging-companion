# Persistent memory — search and recall past sessions from SQLite.
from __future__ import annotations

import re
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.database import session_scope
from src.models import SessionRow


def _tokens(text: str) -> List[str]:
    """Cheap tokeniser: lowercased words, length >= 3, no stopwords."""
    stop = {"the", "and", "for", "with", "from", "into", "that", "this", "your", "you", "are", "but", "not"}
    words = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    return [w for w in words if w not in stop]


class MemoryStore:
    """Lightweight persistent memory over past flow sessions."""

    def recent(self, limit: int = 10) -> List[SessionRow]:
        """Return the most recent sessions."""
        with session_scope() as db:
            return (
                db.query(SessionRow)
                .order_by(SessionRow.started_at.desc())
                .limit(limit)
                .all()
            )

    def search(self, query: str, limit: int = 5) -> List[SessionRow]:
        """Return sessions whose goal / title share tokens with the query."""
        tokens = _tokens(query)
        if not tokens:
            return self.recent(limit=limit)

        with session_scope() as db:
            clauses = []
            for t in tokens[:10]:  # bound the OR-list
                like = f"%{t}%"
                clauses.append(SessionRow.goal.ilike(like))
                clauses.append(SessionRow.title.ilike(like))
            return (
                db.query(SessionRow)
                .filter(or_(*clauses))
                .order_by(SessionRow.started_at.desc())
                .limit(limit)
                .all()
            )

    def by_id(self, session_id: str) -> Optional[SessionRow]:
        with session_scope() as db:
            return db.get(SessionRow, session_id)