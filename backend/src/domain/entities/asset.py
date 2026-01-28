from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Asset:
    symbol: str
    name: str
    category: str
    id: UUID = uuid4()
    created_at: datetime = datetime.now()


