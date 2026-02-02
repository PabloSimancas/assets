from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Identity, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base



class HyperliquidVault(Base):
    __tablename__ = "raw_vaults"
    __table_args__ = (
        Index("idx_hl_vaults_ingested", "vault_address", "ingested_at"),
        {"schema": "bronze"}
    )

    id = Column(Integer, Identity(always=True), primary_key=True)
    vault_address = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    raw_content = Column(Text) # JSON string
    response_metadata = Column(JSONB)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_to_silver = Column(Boolean, default=False)
