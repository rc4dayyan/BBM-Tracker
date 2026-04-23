CREATE TABLE IF NOT EXISTS consumption (
    id BIGSERIAL PRIMARY KEY,
    fuel_type TEXT NOT NULL,
    price REAL NOT NULL,
    current_km REAL NOT NULL,
    distance REAL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mileage (
    id BIGSERIAL PRIMARY KEY,
    odometer_km REAL NOT NULL,
    notes TEXT,
    recorded_at TEXT NOT NULL
);