import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    # Supabase (and most hosted PG) requires SSL; append if not already specified
    url = DATABASE_URL
    if "sslmode" not in url:
        url += "?sslmode=require"
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS consumption (
            id SERIAL PRIMARY KEY,
            fuel_type TEXT NOT NULL,
            price REAL NOT NULL,
            current_km REAL NOT NULL,
            distance REAL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mileage (
            id SERIAL PRIMARY KEY,
            odometer_km REAL NOT NULL,
            notes TEXT,
            recorded_at TEXT NOT NULL
        )
    """)
    db.commit()
    cur.close()
    db.close()
