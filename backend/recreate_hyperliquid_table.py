from src.infrastructure.database.session import engine, Base
from src.infrastructure.database.silver_models import SilverHyperliquidPosition
from src.infrastructure.database.scraping_models import HyperliquidVault
from sqlalchemy import text, inspect

def recreate_hyperliquid_tables():
    print("--- Recreating Hyperliquid Tables to fix Schema Structure ---")
    
    with engine.connect() as conn:
        # 1. Cleanup Legacy Schema
        print("Dropping legacy schema 'hyperliquid_vaults'...")
        conn.execute(text("DROP SCHEMA IF EXISTS hyperliquid_vaults CASCADE"))
        
        # 2. Cleanup unwanted tables (User Request)
        print("Dropping bronze.web_scrapes...")
        conn.execute(text("DROP TABLE IF EXISTS bronze.web_scrapes CASCADE"))
        print("Dropping silver.tickers...")
        conn.execute(text("DROP TABLE IF EXISTS silver.tickers CASCADE"))
        
        # 3. Move Positions to Bronze (Drop old silver location)
        print("Dropping silver.hyperliquid_positions (moving to bronze)...")
        conn.execute(text("DROP TABLE IF EXISTS silver.hyperliquid_positions CASCADE"))
        print("Dropping bronze.hyperliquid_positions (cleanup)...")
        conn.execute(text("DROP TABLE IF EXISTS bronze.hyperliquid_positions CASCADE"))
        print("Dropping silver.hyperliquid_aggregated...")
        conn.execute(text("DROP TABLE IF EXISTS silver.hyperliquid_aggregated CASCADE"))
        print("Dropping gold.hyperliquid_summary...")
        conn.execute(text("DROP TABLE IF EXISTS gold.hyperliquid_summary CASCADE"))
        
        # 4. Ensure Schemas
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver")) # Keep silver empty but existing
        
        conn.commit()

    # 5. Create Tables (SQLAlchemy handles schema based on model __table_args__)
    print("Creating tables...")
    # Only create the specific tables we want (avoiding legacy ones like web_scrapes/tickers if they are still in Base)
    # 1. HyperliquidVault (bronze.raw_vaults)
    HyperliquidVault.__table__.create(bind=engine, checkfirst=True)
    # 2. SilverHyperliquidPosition (bronze.hyperliquid_positions - model name still Silver...)
    SilverHyperliquidPosition.__table__.create(bind=engine, checkfirst=True)
    
    print("Tables created.")

    # verify columns
    inspector = inspect(engine)
    
    print("\nVerifying 'bronze' schema:")
    bronze_tables = inspector.get_table_names(schema='bronze')
    print(f"Tables: {bronze_tables}")
    
    if 'raw_vaults' in bronze_tables:
        cols = inspector.get_columns('raw_vaults', schema='bronze')
        print(f" - raw_vaults columns: {[c['name'] for c in cols]}")

    print("\nVerifying 'silver' schema (Should be empty of tickers/positions):")
    silver_tables = inspector.get_table_names(schema='silver')
    print(f"Tables: {silver_tables}")

    print("\nVerifying 'bronze' schema (Should have raw_vaults and hyperliquid_positions):")
    bronze_tables = inspector.get_table_names(schema='bronze')
    print(f"Tables: {bronze_tables}")
    
    if 'hyperliquid_positions' in bronze_tables:
        columns = inspector.get_columns('hyperliquid_positions', schema='bronze')
        print(" - hyperliquid_positions columns:")
        for col in columns:
            print(f"   - {col['name']} ({col['type']})")

if __name__ == "__main__":
    recreate_hyperliquid_tables()
