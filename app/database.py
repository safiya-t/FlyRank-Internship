"""
Database connection and session management module using SQLAlchemy.
"""

import sys
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings


def get_connection_url(url: str) -> str:
    """
    Ensure the PostgreSQL driver is explicitly set to psycopg2 if unspecified.
    Supports standard 'postgresql://' and legacy 'postgres://' connection strings.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


# Create SQLAlchemy Engine
# pool_pre_ping=True tests connections for liveness before giving them to the pool
engine = create_engine(
    get_connection_url(settings.DATABASE_URL),
    pool_pre_ping=True,
)

# Session factory for generating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Reusable FastAPI dependency providing a transactional database session.
    Closes the session automatically when the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(target_engine=None) -> tuple[bool, str]:
    """
    Tests the database connection by executing a lightweight query (SELECT 1).
    Returns a tuple of (is_successful, message).
    """
    bind_engine = target_engine or engine
    try:
        with bind_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful!"
    except SQLAlchemyError as exc:
        error_msg = (
            f"Database connection failed!\n"
            f"Target URL: {settings.DATABASE_URL}\n"
            f"Error details: {exc}"
        )
        return False, error_msg
    except Exception as exc:
        error_msg = f"Unexpected error while connecting to database: {exc}"
        return False, error_msg


def init_db(target_engine=None) -> None:
    """
    Initializes database tables by creating all tables defined in models.
    Safe for repeated executions (idempotent).
    """
    # Import models so Base.metadata is aware of all table definitions
    import app.models  # noqa: F401

    bind_engine = target_engine or engine
    Base.metadata.create_all(bind=bind_engine)


def main() -> None:
    """Command-line entry point to check database connection and optionally init tables."""
    args = sys.argv[1:]

    print("Testing PostgreSQL database connection...")
    success, message = check_db_connection()

    if not success:
        print(f"[ERROR] {message}\n")
        print("--- Troubleshooting Checklist ---")
        print("1. Service Status: Ensure PostgreSQL service is running.")
        print("2. Credentials: Check user/password in DATABASE_URL inside your .env file.")
        print("3. Database Existence: Ensure the database exists (e.g. 'CREATE DATABASE image_matching_db;').")
        print("4. Network/Port: Ensure port 5432 is accessible on localhost/host.")
        sys.exit(1)

    print(f"[OK] {message}")

    if "--init" in args:
        print("Initializing database tables...")
        try:
            init_db()
            print("[OK] All tables created/verified successfully.")
        except Exception as exc:
            print(f"[ERROR] Failed to initialize tables: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    main()
