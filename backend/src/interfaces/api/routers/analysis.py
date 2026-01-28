from fastapi import APIRouter, HTTPException, Depends
from src.application.services.analysis_service import AnalysisService

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

@router.get("/{symbol}/master")
async def get_master_analysis(symbol: str):
    data = AnalysisService.get_master_analysis(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"No analysis data found for {symbol}")
    return data
