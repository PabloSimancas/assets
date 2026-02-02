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
        
        # 2. Ensure Bronze Schema & Tables
        print("Ensuring 'bronze' schema...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
        
        # 3. Ensure Silver Schema
        print("Ensuring 'silver' schema...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
        
        # 4. Clean Silver Table (Restart)
        print("Dropping silver.hyperliquid_positions...")
        conn.execute(text("DROP TABLE IF EXISTS silver.hyperliquid_positions CASCADE"))
        
        conn.commit()

    # 5. Create Tables (SQLAlchemy handles schema based on model __table_args__)
    print("Creating tables...")
    # This will create bronze.raw_vaults (if missing) and silver.hyperliquid_positions
    Base.metadata.create_all(bind=engine)
    
    print("Tables created.")

    # verify columns
    inspector = inspect(engine)
    
    print("\nVerifying 'bronze' schema:")
    bronze_tables = inspector.get_table_names(schema='bronze')
    print(f"Tables: {bronze_tables}")
    
    if 'raw_vaults' in bronze_tables:
        cols = inspector.get_columns('raw_vaults', schema='bronze')
        print(f" - raw_vaults columns: {[c['name'] for c in cols]}")

    print("\nVerifying 'silver' schema:")
    if 'hyperliquid_positions' in inspector.get_table_names(schema='silver'):
        columns = inspector.get_columns('hyperliquid_positions', schema='silver')
        print(" - hyperliquid_positions columns:")
        for col in columns:
            print(f"   - {col['name']} ({col['type']})")

if __name__ == "__main__":
    recreate_hyperliquid_tables()
