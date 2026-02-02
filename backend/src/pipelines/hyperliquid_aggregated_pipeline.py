"""
Hyperliquid Aggregated Pipeline

Reads from SilverHyperliquidPosition (bronze.hyperliquid_positions),
calculates position direction (Long/Short) and scaled financial values,
writes to SilverHyperliquidAggregated (silver.hyperliquid_aggregated).

Direction Logic:
    IF(OR(AND(mark_price > entry_price, pnl > 0), AND(mark_price < entry_price, pnl < 0)), 1, -1)
    
    1 = Long, -1 = Short

Scaled Values:
    - pos_value_millions_long: position_value / 1,000,000 (only if Long)
    - pos_value_millions_short: -position_value / 1,000,000 (only if Short)
    - margin_thousands_long: margin_used / 1,000 (only if Long)
    - margin_thousands_short: -margin_used / 1,000 (only if Short)
"""

import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy import and_, not_, exists
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.silver_models import (
    SilverHyperliquidPosition, 
    SilverHyperliquidAggregated
)


class HyperliquidAggregatedPipeline:
    def __init__(self):
        self.logger = logging.getLogger("pipeline.hyperliquid_aggregated")
        self.db = SessionLocal()

    def run(self):
        self.logger.info("Starting Hyperliquid Aggregated Pipeline (Silver Positions -> Silver Aggregated)")
        try:
            self._process_positions()
            self.db.commit()
            self.logger.info("Hyperliquid Aggregated Pipeline completed successfully.")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Aggregated Pipeline failed: {e}")
        finally:
            self.db.close()

    def _process_positions(self):
        """
        Reads unprocessed positions from SilverHyperliquidPosition,
        calculates direction and scaled values, inserts into SilverHyperliquidAggregated.
        """
        # Get positions that haven't been aggregated yet
        # We check by seeing if source_position_id already exists in the aggregated table
        subquery = self.db.query(SilverHyperliquidAggregated.source_position_id)
        
        positions = self.db.query(SilverHyperliquidPosition).filter(
            not_(SilverHyperliquidPosition.id.in_(subquery))
        ).limit(100).all()

        if not positions:
            self.logger.info("No new positions to aggregate.")
            return

        created_count = 0
        for pos in positions:
            try:
                # Calculate direction
                direction = self._calculate_direction(
                    mark_price=pos.mark_price,
                    entry_price=pos.entry_price,
                    unrealized_pnl=pos.unrealized_pnl
                )

                # Calculate scaled values based on direction
                pos_value_millions_long = None
                pos_value_millions_short = None
                margin_thousands_long = None
                margin_thousands_short = None

                position_value = float(pos.position_value) if pos.position_value else 0
                margin_used = float(pos.margin_used) if pos.margin_used else 0

                if direction == 1:  # Long
                    pos_value_millions_long = position_value / 1_000_000
                    margin_thousands_long = margin_used / 1_000
                else:  # Short
                    pos_value_millions_short = -position_value / 1_000_000
                    margin_thousands_short = -margin_used / 1_000

                # Create aggregated record
                aggregated = SilverHyperliquidAggregated(
                    source_position_id=pos.id,
                    vault_address=pos.vault_address,
                    user_address=pos.user_address,
                    coin=pos.coin,
                    
                    # Copy base data
                    entry_price=pos.entry_price,
                    mark_price=pos.mark_price,
                    position_size=pos.position_size,
                    position_value=pos.position_value,
                    margin_used=pos.margin_used,
                    unrealized_pnl=pos.unrealized_pnl,
                    
                    # Calculated fields
                    direction=direction,
                    pos_value_millions_long=pos_value_millions_long,
                    pos_value_millions_short=pos_value_millions_short,
                    margin_thousands_long=margin_thousands_long,
                    margin_thousands_short=margin_thousands_short,
                    
                    timestamp=pos.timestamp
                )
                self.db.add(aggregated)
                created_count += 1

            except Exception as e:
                self.logger.error(f"Error processing position {pos.id}: {e}")

        self.logger.info(f"Created {created_count} aggregated records from {len(positions)} positions.")

    def _calculate_direction(
        self, 
        mark_price: Optional[Decimal], 
        entry_price: Optional[Decimal], 
        unrealized_pnl: Optional[Decimal]
    ) -> int:
        """
        Calculate position direction based on price movement and P&L.
        
        Logic:
            IF(OR(AND(mark > entry, pnl > 0), AND(mark < entry, pnl < 0)), 1, -1)
        
        Returns:
            1 = Long
            -1 = Short
        """
        # Handle None/zero values
        mark = float(mark_price) if mark_price else 0
        entry = float(entry_price) if entry_price else 0
        pnl = float(unrealized_pnl) if unrealized_pnl else 0

        # Scenario A: mark > entry AND pnl > 0 -> Long in profit
        # Scenario B: mark < entry AND pnl < 0 -> Long in loss
        if (mark > entry and pnl > 0) or (mark < entry and pnl < 0):
            return 1  # Long
        else:
            return -1  # Short
