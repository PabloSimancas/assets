from src.infrastructure.database.session import SessionLocal, engine
from src.infrastructure.database.models import Base, AssetModel
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

    # 1. Execute Master Schema (creates crypto_forwards schema and tables)
    schema_path = os.path.join("src", "infrastructure", "database", "master_schema.sql")
    if os.path.exists(schema_path):
        print(f"Executing schema from {schema_path}...")
        try:
            with open(schema_path, "r") as f:
                sql_statements = f.read()
                # Use a new connection for schema execution
                with engine.connect() as connection:
                    connection.execute(text(sql_statements))
                    connection.commit()
            print("Schema executed successfully.")
        except Exception as e:
            print(f"ERROR executing schema: {e}")
    else:
        print(f"Warning: Schema file not found at {schema_path}")

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
    print("Running Base.metadata.create_all...")
    try:
        Base.metadata.create_all(bind=engine)
        print("create_all completed.")
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
        if "relation \"assets\" does not exist" in str(e):
             print("CRITICAL: 'assets' table still missing after create_all. Attempting forceful recreation...")
             try:
                db.rollback()
                AssetModel.__table__.create(engine)
                print("Force creation successful.")
                # Recursively call or just exit and let restart handle?
                # Let's just return, next run will seed.
             except Exception as create_err:
                 print(f"Force creation failed: {create_err}")
        else:
            print(f"Database Error: {e}")
    except Exception as e:
        print(f"Unexpected error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_assets()
