CREATE TABLE IF NOT EXISTS vehicles (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    plate TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consumption (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE,
    fuel_type TEXT NOT NULL,
    price REAL NOT NULL,
    current_km REAL NOT NULL,
    distance REAL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mileage (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE,
    odometer_km REAL NOT NULL,
    notes TEXT,
    recorded_at TEXT NOT NULL
);