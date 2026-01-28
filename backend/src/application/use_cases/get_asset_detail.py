from src.application.ports.asset_repository import AssetRepository
from src.application.dtos.asset import AssetDetailDTO

class GetAssetDetailUseCase:
    def __init__(self, repository: AssetRepository):
        self.repository = repository

    def execute(self, symbol: str) -> AssetDetailDTO:
        asset = self.repository.get_by_symbol(symbol)
        if not asset:
            raise ValueError(f"Asset with symbol {symbol} not found")

        return AssetDetailDTO(
            symbol=asset.symbol,
            name=asset.name,
            category=asset.category
        )
