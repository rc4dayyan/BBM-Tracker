-- Run this in your Supabase SQL editor to add vehicle support

-- 1. Create vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'ICE',
    notes TEXT,
    created_at TEXT NOT NULL
);

-- 2. Add vehicle_id column to existing tables (nullable to preserve old data)
ALTER TABLE consumption ADD COLUMN IF NOT EXISTS vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE;
ALTER TABLE mileage ADD COLUMN IF NOT EXISTS vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE;
