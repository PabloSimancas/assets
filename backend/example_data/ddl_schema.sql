-- Create schema
CREATE SCHEMA IF NOT EXISTS cryptodata;

-- Optional: make cryptodata the default schema for this session
SET search_path TO cryptodata, public;

-- ---------- 1) ENUM types (in cryptodata schema) ----------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'asset_symbol' AND n.nspname = 'cryptodata'
  ) THEN
    CREATE TYPE cryptodata.asset_symbol AS ENUM ('BTC', 'ETH');
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'curve_shape' AND n.nspname = 'cryptodata'
  ) THEN
    CREATE TYPE cryptodata.curve_shape AS ENUM ('Backwardation', 'Flat', 'Contango');
  END IF;
END $$;

-- ---------- 2) Main table: cryptodata.run_main ----------
CREATE TABLE IF NOT EXISTS cryptodata.run_main (
    run_main_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    asset      cryptodata.asset_symbol NOT NULL,
    ran_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),

    source     TEXT NOT NULL DEFAULT 'deribit',
    spot_price NUMERIC(20,8)
);

-- ---------- 3) Child table: cryptodata.run_details ----------
CREATE TABLE IF NOT EXISTS cryptodata.run_details (
    detail_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_main_id    BIGINT NOT NULL,
    expiry_str    TEXT,
    expiry_date    DATE NOT NULL,
    days_to_expiry INTEGER NOT NULL CHECK (days_to_expiry >= 0),

    future_price   NUMERIC(20,8) NOT NULL,
    open_interest  NUMERIC(30,2) NOT NULL CHECK (open_interest >= 0),
    spot_price     NUMERIC(20,8) NOT NULL,

    premium_pct    NUMERIC(10,6) NOT NULL,
    annualized_pct NUMERIC(10,6) NOT NULL,
    curve          cryptodata.curve_shape NOT NULL,

    instrument_name TEXT,

    CONSTRAINT fk_run_details_run_main
      FOREIGN KEY (run_main_id)
      REFERENCES cryptodata.run_main (run_main_id)
      ON DELETE CASCADE,

    CONSTRAINT uq_run_details_run_expiry
      UNIQUE (run_main_id, expiry_date)
);

-- ---------- 4) Indexes ----------
CREATE INDEX IF NOT EXISTS idx_run_main_asset_time
    ON cryptodata.run_main (asset, ran_at_utc);

CREATE INDEX IF NOT EXISTS idx_run_main_time
    ON cryptodata.run_main (ran_at_utc);

CREATE INDEX IF NOT EXISTS idx_run_details_run_main
    ON cryptodata.run_details (run_main_id);

CREATE INDEX IF NOT EXISTS idx_run_details_expiry
    ON cryptodata.run_details (expiry_date);
