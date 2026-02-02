from src.infrastructure.database.session import engine, Base
from src.infrastructure.database.silver_models import SilverHyperliquidPosition
from sqlalchemy import text, inspect

def recreate_hyperliquid_tables():
    print("Recreating Silver Hyperliquid Position table...")
    
    # Create schema if not exists
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
        conn.commit()

    # Drop specific table if exists
    # We use engine.connect to execute raw SQL for safety or use metadata.drop_all with specific tables
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS silver.hyperliquid_positions CASCADE"))
        conn.commit()
        print("Dropped silver.hyperliquid_positions")

    # Create tables
    # We only want to create this specific table to avoid messing up others
    SilverHyperliquidPosition.__table__.create(bind=engine)
    print("Created silver.hyperliquid_positions with new schema.")

    # verify columns
    inspector = inspect(engine)
    columns = inspector.get_columns('hyperliquid_positions', schema='silver')
    print("\nVerifying columns in silver.hyperliquid_positions:")
    for col in columns:
        print(f" - {col['name']} ({col['type']})")

if __name__ == "__main__":
    recreate_hyperliquid_tables()
