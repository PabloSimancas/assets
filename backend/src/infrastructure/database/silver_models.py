from sqlalchemy import Column, String, Numeric, DateTime, Text, BigInteger, Identity, Index
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class SilverTicker(Base):
    __tablename__ = "tickers"
    __table_args__ = (
        Index("idx_silver_tickers_asset_time", "asset_symbol", "timestamp"),
        {"schema": "silver"}
    )

    id = Column(BigInteger, Identity(always=True), primary_key=True)
    asset_symbol = Column(String(20), nullable=False) # BTC, ETH
    instrument_name = Column(String(100), nullable=False) # BTC-29MAR24
    price = Column(Numeric(20, 8), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source_origin = Column(String(50)) # deribit
