from typing import List
from src.application.ports.asset_repository import AssetRepository
from src.application.dtos.asset import AssetSummaryDTO

class ListAssetsUseCase:
    def __init__(self, repository: AssetRepository):
        self.repository = repository

    def execute(self) -> List[AssetSummaryDTO]:
        assets = self.repository.list_all()
        return [
            AssetSummaryDTO(
                symbol=asset.symbol,
                name=asset.name,
                category=asset.category
            ) for asset in assets
        ]
