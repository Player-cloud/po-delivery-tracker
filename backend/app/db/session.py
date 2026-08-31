from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping + a short recycle keep the pool healthy against a managed
# Postgres that drops idle connections or scales to zero (Neon in production).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session]:
    """FastAPI dependency: yields a request-scoped DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
