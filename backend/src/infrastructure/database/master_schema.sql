-- Master Database Schema
-- Includes core application tables and crypto forward data analytics

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. CORE ASSETS SCHEMA (public)
-- Assets table is managed by SQLAlchemy ORM (models.py) to use UUID primary keys.


-- 3. CRYPTO FORWARDS DATA SCHEMA
CREATE SCHEMA IF NOT EXISTS crypto_forwards;

-- ENUMs for Crypto Data
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'asset_symbol') THEN
        CREATE TYPE crypto_forwards.asset_symbol AS ENUM ('BTC', 'ETH');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'curve_shape') THEN
        CREATE TYPE crypto_forwards.curve_shape AS ENUM ('Backwardation', 'Flat', 'Contango');
    END IF;
END$$;

-- Main Run Table
CREATE TABLE IF NOT EXISTS crypto_forwards.run_main (
    run_main_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset crypto_forwards.asset_symbol NOT NULL,
    ran_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL DEFAULT 'deribit',
    spot_price NUMERIC(20, 8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Run Details Table
CREATE TABLE IF NOT EXISTS crypto_forwards.run_details (
    detail_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_main_id BIGINT NOT NULL,
    expiry_str TEXT,
    expiry_date DATE NOT NULL,
    days_to_expiry INTEGER NOT NULL CHECK (days_to_expiry >= 0),
    future_price NUMERIC(20, 8) NOT NULL,
    open_interest NUMERIC(30, 2) NOT NULL CHECK (open_interest >= 0),
    spot_price NUMERIC(20, 8) NOT NULL,
    premium_pct NUMERIC(10, 6) NOT NULL,
    annualized_pct NUMERIC(10, 6) NOT NULL,
    curve crypto_forwards.curve_shape NOT NULL,
    instrument_name TEXT,
    CONSTRAINT fk_run_details_run_main FOREIGN KEY (run_main_id) REFERENCES crypto_forwards.run_main (run_main_id) ON DELETE CASCADE,
    CONSTRAINT uq_run_details_run_expiry UNIQUE (run_main_id, expiry_date)
);

-- Indexes for Analytics
CREATE INDEX IF NOT EXISTS idx_run_main_asset_time ON crypto_forwards.run_main (asset, ran_at_utc);
CREATE INDEX IF NOT EXISTS idx_run_details_expiry ON crypto_forwards.run_details (expiry_date);
