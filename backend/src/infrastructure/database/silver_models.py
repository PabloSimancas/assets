from sqlalchemy import Column, String, Numeric, DateTime, BigInteger, Identity, Index, JSON, Integer
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base



class SilverHyperliquidPosition(Base):
    __tablename__ = "hyperliquid_positions"
    __table_args__ = (
        Index("idx_hl_pos_vault_time", "vault_address", "timestamp"),
        {"schema": "bronze"}
    )

    id = Column(BigInteger, Identity(always=True), primary_key=True)
    vault_address = Column(String(50), nullable=False)
    user_address = Column(String(50), nullable=True) # Child address if applicable
    coin = Column(String(20), nullable=False) # e.g. BTC
    
    # Financial Data
    entry_price = Column(Numeric(30, 8))
    mark_price = Column(Numeric(30, 8)) # Derived: val / size
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
    
class SilverHyperliquidAggregated(Base):
    """
    Aggregated/calculated fields derived from SilverHyperliquidPosition.
    Contains position direction (Long/Short) and scaled financial values.
    """
    __tablename__ = "hyperliquid_aggregated"
    __table_args__ = (
        Index("idx_hl_agg_vault_time", "vault_address", "timestamp"),
        Index("idx_hl_agg_source_id", "source_position_id"),
        {"schema": "silver"}
    )

    id = Column(BigInteger, Identity(always=True), primary_key=True)
    source_position_id = Column(BigInteger, nullable=False)  # Reference to SilverHyperliquidPosition.id
    vault_address = Column(String(50), nullable=False)
    user_address = Column(String(50), nullable=True)
    coin = Column(String(20), nullable=False)
    
    # Original base data (for reference/convenience)
    entry_price = Column(Numeric(30, 8))
    mark_price = Column(Numeric(30, 8))
    position_size = Column(Numeric(30, 8))
    position_value = Column(Numeric(30, 8))
    margin_used = Column(Numeric(30, 8))
    unrealized_pnl = Column(Numeric(30, 8))
    
    # Calculated fields
    direction = Column(Integer)  # 1 = Long, -1 = Short
    
    # Scaled values - only populated for the relevant direction
    # Position value scaled by 1,000,000 (millions)
    pos_value_millions_long = Column(Numeric(20, 6), nullable=True)
    pos_value_millions_short = Column(Numeric(20, 6), nullable=True)
    # Margin scaled by 1,000 (thousands)
    margin_thousands_long = Column(Numeric(20, 6), nullable=True)
    margin_thousands_short = Column(Numeric(20, 6), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

