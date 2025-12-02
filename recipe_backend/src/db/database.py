import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load environment variables from .env if present
load_dotenv()

# Resolve DATABASE_URL with default to local SQLite file
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Configure SQLAlchemy engine
# For SQLite, need check_same_thread=False for use in FastAPI with multiple threads
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

# SQLAlchemy ORM Base
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session, future=True)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures proper close.

    Yields:
        Session: SQLAlchemy ORM session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def create_all_tables() -> None:
    """Create all tables defined on the declarative Base metadata.

    This helper can be called at application startup to ensure the database schema exists.
    """
    # Import models here to ensure they are registered with Base.metadata
    # (Avoid circular imports in other modules)
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for ad-hoc session usage outside FastAPI dependency."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
