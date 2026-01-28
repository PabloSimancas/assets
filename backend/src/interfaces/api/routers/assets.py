from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.asset_repository import SQLAlchemyAssetRepository
from src.application.use_cases.get_asset_detail import GetAssetDetailUseCase
from typing import List
from src.application.use_cases.list_assets import ListAssetsUseCase
from src.application.dtos.asset import AssetDetailDTO, AssetSummaryDTO

router = APIRouter(
    prefix="/assets",
    tags=["assets"]
)

@router.get("/", response_model=List[AssetSummaryDTO])
async def list_assets(db: Session = Depends(get_db)):
    repository = SQLAlchemyAssetRepository(db)
    use_case = ListAssetsUseCase(repository)
    return use_case.execute()

@router.get("/{symbol}", response_model=AssetDetailDTO)
async def get_asset_detail(symbol: str, db: Session = Depends(get_db)):
    repository = SQLAlchemyAssetRepository(db)
    use_case = GetAssetDetailUseCase(repository)
    try:
        return use_case.execute(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
