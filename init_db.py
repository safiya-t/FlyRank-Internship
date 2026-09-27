"""
Database initialization script to create all tables for local development.
Safe to run repeatedly (idempotent).
"""
import sys
from app.database import check_db_connection, init_db

if __name__ == "__main__":
    print("Testing connection before initialization...")
    success, message = check_db_connection()
    if not success:
        print(f"[ERROR] Cannot initialize tables: {message}")
        sys.exit(1)

    print(f"[OK] {message}")
    print("Creating tables in PostgreSQL database...")
    try:
        init_db()
        print("[SUCCESS] All tables initialized successfully!")
    except Exception as exc:
        print(f"[ERROR] Table initialization failed: {exc}")
        sys.exit(1)
