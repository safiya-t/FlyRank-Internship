from dotenv import load_dotenv
import os
import psycopg
import time
from supabase import create_client

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_connection():
    for i in range(10):
        try:
            return psycopg.connect(DATABASE_URL)
        except psycopg.OperationalError:
            print(f"Database not ready, retrying... ({i+1}/10)")
            time.sleep(2)

    raise Exception("Could not connect to PostgreSQL")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Buy groceries", False),
                ("Complete assignments", False),
                ("Practice DSA", False),
            ],
        )

    conn.commit()
    cursor.close()
    conn.close()