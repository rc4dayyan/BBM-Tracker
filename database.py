import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db() -> Client:
    return _client

def init_db():
    # Tables are managed in the Supabase dashboard / SQL editor.
    # Run the following SQL once in Supabase SQL Editor:
    #
    # CREATE TABLE IF NOT EXISTS consumption (
    #     id BIGSERIAL PRIMARY KEY,
    #     fuel_type TEXT NOT NULL,
    #     price REAL NOT NULL,
    #     current_km REAL NOT NULL,
    #     distance REAL,
    #     notes TEXT,
    #     created_at TEXT NOT NULL
    # );
    #
    # CREATE TABLE IF NOT EXISTS mileage (
    #     id BIGSERIAL PRIMARY KEY,
    #     odometer_km REAL NOT NULL,
    #     notes TEXT,
    #     recorded_at TEXT NOT NULL
    # );
    pass
