from sqlalchemy import text
from src.infrastructure.database.session import SessionLocal, engine
from src.infrastructure.database.models import AssetModel
import sys

def check_db():
    print(f"Checking Database: {engine.url}")
    db = SessionLocal()
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        print("Database connection successful.")
        
        assets = db.query(AssetModel).all()
        print(f"Found {len(assets)} assets in DB:")
        for a in assets:
            print(f"- {a.symbol}: {a.name}")
    except Exception as e:
        print(f"Error checking DB: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
