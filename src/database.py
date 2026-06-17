# Database wiring — SQLAlchemy session factory and base class.
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings

_settings = get_settings()

# `check_same_thread=False` is required for SQLite + FastAPI's thread pool.
_connect_args = {"check_same_thread": False} if _settings.db_url.startswith("sqlite") else {}

engine = create_engine(_settings.db_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base used by all ORM models."""
    pass


def init_db() -> None:
    """Create all tables. Safe to call repeatedly — no-op if already up-to-date."""
    # Importing models registers them with Base.metadata.
    from src import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()