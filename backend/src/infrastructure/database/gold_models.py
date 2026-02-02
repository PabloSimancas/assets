"""
Gold Layer Models for Hyperliquid

Aggregated summary data grouped by timestamp from silver.hyperliquid_aggregated.
"""

from sqlalchemy import Column, Numeric, DateTime, BigInteger, Identity, Index, Integer
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base


class GoldHyperliquidSummary(Base):
    """
    Gold layer: Time-grouped aggregates from silver.hyperliquid_aggregated.
    
    Each row represents a single timestamp with summed metrics across all positions.
    
    Column Reference (Dashboard Labels):
        - total_position_value_millions: xMil$ (net sum of longs + shorts)
        - longs_position_value_millions:  TS.L (sum of long positions, positive)
        - shorts_position_value_millions: TS.S (sum of short positions, negative)
        - longs_margin_thousands:         M$.L (sum of long margins, positive)
        - shorts_margin_thousands:        M$.S (sum of short margins, negative)
        - net_margin_thousands:           net M$ (longs + shorts margin)
    """
    __tablename__ = "hyperliquid_summary"
    __table_args__ = (
        Index("idx_hl_gold_timestamp", "timestamp"),
        {"schema": "gold"}
    )
    
    id = Column(BigInteger, Identity(always=True), primary_key=True)
    
    # Aggregated Position Values (scaled by 1,000,000)
    total_position_value_millions = Column(Numeric(20, 6))   # SUM(longs) + SUM(shorts) = net
    longs_position_value_millions = Column(Numeric(20, 6))   # SUM(pos_value_millions_long)
    shorts_position_value_millions = Column(Numeric(20, 6))  # SUM(pos_value_millions_short) - negative
    
    # Aggregated Margin Values (scaled by 1,000)
    longs_margin_thousands = Column(Numeric(20, 6))          # SUM(margin_thousands_long)
    shorts_margin_thousands = Column(Numeric(20, 6))         # SUM(margin_thousands_short) - negative
    net_margin_thousands = Column(Numeric(20, 6))            # longs + shorts margin
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, unique=True)
    position_count = Column(Integer)                          # Number of positions in this snapshot
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
