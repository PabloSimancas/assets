from src.infrastructure.database.session import SessionLocal, engine
from src.infrastructure.database.models import Base, AssetModel
import uuid

def init_assets():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already have assets
    existing_count = db.query(AssetModel).count()
    if existing_count > 0:
        print(f"Database already has {existing_count} assets. Skipping seed.")
        db.close()
        return

    # Static data only (Symbol, Name, Category)
    assets_data = [
        {"symbol": "BTC", "name": "Bitcoin", "category": "Crypto"},
        {"symbol": "ETH", "name": "Ethereum", "category": "Crypto"},
        {"symbol": "GOLD", "name": "Gold", "category": "Commodity"},
        {"symbol": "SPX", "name": "S&P 500", "category": "Index"},
        {"symbol": "TSLA", "name": "Tesla", "category": "Stock"},
    ]
    
    for data in assets_data:
        asset = AssetModel(
            id=uuid.uuid4(),
            symbol=data["symbol"],
            name=data["name"],
            category=data["category"]
        )
        db.add(asset)
            
    db.commit()
    db.close()
    print("Static assets initialized successfully!")

if __name__ == "__main__":
    init_assets()
