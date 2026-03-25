"""Database engine, session management, and startup initialization."""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.utils.config import get_settings
from app.utils.logging import get_logger


settings = get_settings()
logger = get_logger(__name__)

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def _ensure_sqlite_indexes() -> None:
    """Apply SQLite-safe schema guards for existing production databases."""
    if not is_sqlite:
        return

    inspector = inspect(engine)
    if "crop_diseases" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("crop_diseases")}

    with engine.begin() as connection:
        if "disease_name" not in columns:
            logger.info("Adding missing crop_diseases.disease_name column.")
            connection.execute(
                text(
                    "ALTER TABLE crop_diseases "
                    "ADD COLUMN disease_name VARCHAR(150) DEFAULT 'Unknown'"
                )
            )

        connection.execute(
            text(
                "UPDATE crop_diseases "
                "SET disease_name = 'Unknown-' || id "
                "WHERE disease_name IS NULL OR TRIM(disease_name) = ''"
            )
        )

        connection.execute(
            text(
                "WITH duplicate_rows AS ("
                "  SELECT id, ROW_NUMBER() OVER ("
                "    PARTITION BY crop_name, disease_name ORDER BY id"
                "  ) AS row_num "
                "  FROM crop_diseases"
                ") "
                "UPDATE crop_diseases "
                "SET disease_name = disease_name || '-' || id "
                "WHERE id IN (SELECT id FROM duplicate_rows WHERE row_num > 1)"
            )
        )

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_disease_pair "
                "ON crop_diseases (crop_name, disease_name)"
            )
        )


def init_db() -> None:
    """Create all tables and apply lightweight startup database guards."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_indexes()


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
