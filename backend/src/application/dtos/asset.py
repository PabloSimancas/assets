from typing import List
from pydantic import BaseModel

class AssetSummaryDTO(BaseModel):
    symbol: str
    name: str
    category: str

    class Config:
        from_attributes = True

class AssetDetailDTO(BaseModel):
    symbol: str
    name: str
    category: str

    class Config:
        from_attributes = True
