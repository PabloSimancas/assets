from sqlalchemy import Column, String, Numeric, DateTime, BigInteger, Identity, Index, JSON, Integer
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

class SilverHyperliquidPosition(Base):
    __tablename__ = "hyperliquid_positions"
    __table_args__ = (
        Index("idx_hl_pos_vault_time", "vault_address", "timestamp"),
        {"schema": "silver"}
    )

    id = Column(BigInteger, Identity(always=True), primary_key=True)
    vault_address = Column(String(50), nullable=False)
    user_address = Column(String(50), nullable=True) # Child address if applicable
    coin = Column(String(20), nullable=False) # e.g. BTC
    
    # Financial Data
    entry_price = Column(Numeric(30, 8))
    position_size = Column(Numeric(30, 8)) # szi
    position_value = Column(Numeric(30, 8)) 
    margin_used = Column(Numeric(30, 8))
    unrealized_pnl = Column(Numeric(30, 8))
    return_on_equity = Column(Numeric(10, 8))
    liquidation_px = Column(Numeric(30, 8), nullable=True)
    max_leverage = Column(Integer)
    
    # Leverage Info (Expanded)
    leverage_type = Column(String(20)) # e.g., 'cross'
    leverage_value = Column(Integer)
    
    # Funding Info
    cum_funding_all_time = Column(Numeric(30, 8))
    cum_funding_since_open = Column(Numeric(30, 8))
    cum_funding_since_change = Column(Numeric(30, 8))
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source_origin = Column(String(50)) # hyperliquid
    
# Force update

