from typing import List, Optional
from sqlalchemy.orm import Session
from src.domain.entities.asset import Asset
from src.application.ports.asset_repository import AssetRepository
from src.infrastructure.database.models import AssetModel

class SQLAlchemyAssetRepository(AssetRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        model = self.db.query(AssetModel).filter(AssetModel.symbol == symbol).first()
        if not model:
            return None
        return Asset(
            id=model.id,
            symbol=model.symbol,
            name=model.name,
            category=model.category,
            created_at=model.created_at
        )

    def list_all(self) -> List[Asset]:
        models = self.db.query(AssetModel).all()
        return [
            Asset(
                id=m.id,
                symbol=m.symbol,
                name=m.name,
                category=m.category,
                created_at=m.created_at
            ) for m in models
        ]
