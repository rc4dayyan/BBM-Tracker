import sqlite3
import os

DATABASE = os.environ.get("DATABASE_PATH", "/data/bbm_tracker.db")

def get_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fuel_type TEXT NOT NULL,
            price REAL NOT NULL,
            current_km REAL NOT NULL,
            distance REAL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS mileage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            odometer_km REAL NOT NULL,
            notes TEXT,
            recorded_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()
