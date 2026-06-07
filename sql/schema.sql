-- ============================================
-- BRONZE LAYER
-- Raw, unprocessed API responses
-- ============================================
CREATE TABLE IF NOT EXISTS raw_rates (
    id SERIAL PRIMARY KEY,
    fetch_date DATE NOT NULL,
    base_currency VARCHAR(3) NOT NULL,
    raw_json TEXT NOT NULL,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SILVER LAYER
-- Cleaned and validated data
-- ============================================
CREATE TABLE IF NOT EXISTS cleaned_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(18, 6) NOT NULL,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, base_currency, target_currency)
);

-- ============================================
-- GOLD LAYER - Dimension Tables
-- ============================================
CREATE TABLE IF NOT EXISTS dim_currencies (
    currency_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10),
    country VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_dates (
    date DATE PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    is_weekday BOOLEAN NOT NULL
);

INSERT INTO dim_currencies (currency_code, name, symbol, country) VALUES
('USD', 'US Dollar', '$', 'United States'),
('EUR', 'Euro', '€', 'European Union'),
('GBP', 'British Pound', '£', 'United Kingdom'),
('RUB', 'Russian Ruble', '₽', 'Russia'),
('UZS', 'Uzbek Som', 'som', 'Uzbekistan')
ON CONFLICT (currency_code) DO NOTHING;

-- ============================================
-- GOLD LAYER - Fact Table
-- ============================================
CREATE TABLE IF NOT EXISTS aggregated_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL REFERENCES dim_dates(date),
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL REFERENCES dim_currencies(currency_code),
    exchange_rate DECIMAL(18, 6) NOT NULL,
    rate_change_pct DECIMAL(10, 4),
    seven_day_avg DECIMAL(18, 6),
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, base_currency, target_currency)
);