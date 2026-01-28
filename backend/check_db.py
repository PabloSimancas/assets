from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.models import AssetModel

def check_db():
    db = SessionLocal()
    assets = db.query(AssetModel).all()
    print(f"Found {len(assets)} assets in DB:")
    for a in assets:
        print(f"- {a.symbol}: {a.name}")
    db.close()

if __name__ == "__main__":
    check_db()
