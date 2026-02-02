from src.infrastructure.database.session import SessionLocal, engine
from src.infrastructure.database.models import Base, AssetModel
# Register new models for creation
from src.infrastructure.database.scraping_models import WebScrape
from src.infrastructure.database.silver_models import SilverTicker, SilverHyperliquidPosition
import uuid
from sqlalchemy import text, inspect, Integer
from sqlalchemy.exc import ProgrammingError, OperationalError
import os
import time

def init_assets():
    # Log connection info (mask password)
    url_str = str(engine.url)
    if ":" in url_str and "@" in url_str:
        # Simple mask
        pass
    print(f"Seed Script - Database: {url_str.split('@')[-1] if '@' in url_str else url_str}")

    # 1. Ensure Schemas Exists (SQLAlchemy requires it before creating tables in it)
    print("Ensuring schemas exist...")
    try:
        with engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS crypto_forwards;"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
            connection.commit()
        print("Schemas ensured.")
    except Exception as e:
        print(f"ERROR ensuring schema exists: {e}")


    # 2. Check for Old Schema (Migration)
    try:
        inspector = inspect(engine)
        if inspector.has_table("assets"):
            columns = inspector.get_columns("assets")
            id_column = next((c for c in columns if c["name"] == "id"), None)
            if id_column and isinstance(id_column["type"], Integer):
                print("DETECTED OLD SCHEMA (ID is Integer). Dropping table 'assets' to migrate to UUID...")
                AssetModel.__table__.drop(engine)
                print("Table dropped.")
    except Exception as e:
        print(f"Error checking schema: {e}")

    # 3. Ensure Tables Exist
    print(f"Registered tables in Base.metadata: {Base.metadata.tables.keys()}")
    print("Running Base.metadata.create_all...")
    try:
        Base.metadata.create_all(bind=engine)
        print("create_all completed.")
        
        # Verify creation immediately
        inspector = inspect(engine)
        if not inspector.has_table("assets"):
             print("WARNING: 'assets' table not found after create_all! Attempting explicit create...")
             AssetModel.__table__.create(engine)
             print("Explicit create called.")
             if not inspector.has_table("assets"):
                  print("CRITICAL: 'assets' table STILL not found after explicit create.")
             else:
                  print("Explicit create SUCCESSFUL.")
        else:
             print("Table 'assets' verified existing.")

    except Exception as e:
        print(f"CRITICAL ERROR during create_all: {e}")
        # Identify if we should exit? Let's try to proceed.

    db = SessionLocal()
    
    # 4. Check/Seed Data
    try:
        existing_count = db.query(AssetModel).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} assets. Skipping seed.")
            db.close()
            return

        # Static data
        assets_data = [
            {"symbol": "BTC", "name": "Bitcoin", "category": "Crypto"},
            {"symbol": "ETH", "name": "Ethereum", "category": "Crypto"},
            {"symbol": "GOLD", "name": "Gold", "category": "Commodity"},
            {"symbol": "SPX", "name": "S&P 500", "category": "Index"},
            {"symbol": "TSLA", "name": "Tesla", "category": "Stock"},
        ]
        
        print("Seeding initial assets...")
        for data in assets_data:
            asset = AssetModel(
                id=uuid.uuid4(),
                symbol=data["symbol"],
                name=data["name"],
                category=data["category"]
            )
            db.add(asset)
                
        db.commit()
        print("Static assets initialized successfully!")
    
    except ProgrammingError as e:
        print(f"Database Error: {e}")
        if "relation \"assets\" does not exist" in str(e):
             print("CRITICAL: 'assets' table still missing after create_all checks.")
    except Exception as e:
        print(f"Unexpected error seeding data: {e}")
        db.rollback()
        import sys
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    init_assets()
