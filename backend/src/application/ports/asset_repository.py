from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.asset import Asset

class AssetRepository(ABC):
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        pass

    @abstractmethod
    def list_all(self) -> List[Asset]:
        pass


