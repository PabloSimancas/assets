from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base
import uuid

class AssetModel(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


