"""
Hyperliquid Gold Pipeline

Reads from silver.hyperliquid_aggregated, groups by timestamp,
and writes aggregated summaries to gold.hyperliquid_summary.

Aggregation Logic:
    - total_position_value_millions: SUM(longs) + SUM(shorts) = net value
    - longs_position_value_millions:  SUM(pos_value_millions_long)
    - shorts_position_value_millions: SUM(pos_value_millions_short)  [negative values]
    - longs_margin_thousands:         SUM(margin_thousands_long)
    - shorts_margin_thousands:        SUM(margin_thousands_short)    [negative values]
    - net_margin_thousands:           longs_margin + shorts_margin
"""

import logging
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import insert
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.silver_models import SilverHyperliquidAggregated
from src.infrastructure.database.gold_models import GoldHyperliquidSummary


class HyperliquidGoldPipeline:
    def __init__(self):
        self.logger = logging.getLogger("pipeline.hyperliquid_gold")
        self.db = SessionLocal()

    def run(self):
        self.logger.info("Starting Hyperliquid Gold Pipeline (Silver Aggregated -> Gold Summary)")
        try:
            self._aggregate_to_gold()
            self.db.commit()
            self.logger.info("Hyperliquid Gold Pipeline completed successfully.")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Gold Pipeline failed: {e}")
        finally:
            self.db.close()

    def _aggregate_to_gold(self):
        """
        Groups silver.hyperliquid_aggregated by timestamp and inserts aggregated
        summaries into gold.hyperliquid_summary.
        
        Skips timestamps that already exist in the gold table.
        """
        # Get timestamps that already exist in gold
        existing_timestamps = self.db.query(GoldHyperliquidSummary.timestamp).subquery()

        # Aggregate query grouped by timestamp
        aggregated = (
            self.db.query(
                SilverHyperliquidAggregated.timestamp,
                # Position values (millions)
                func.sum(func.coalesce(SilverHyperliquidAggregated.pos_value_millions_long, 0)).label('longs_pos'),
                func.sum(func.coalesce(SilverHyperliquidAggregated.pos_value_millions_short, 0)).label('shorts_pos'),
                # Margin values (thousands)
                func.sum(func.coalesce(SilverHyperliquidAggregated.margin_thousands_long, 0)).label('longs_margin'),
                func.sum(func.coalesce(SilverHyperliquidAggregated.margin_thousands_short, 0)).label('shorts_margin'),
                # Count
                func.count().label('position_count')
            )
            .filter(~SilverHyperliquidAggregated.timestamp.in_(existing_timestamps))
            .group_by(SilverHyperliquidAggregated.timestamp)
            .all()
        )

        if not aggregated:
            self.logger.info("No new timestamps to aggregate to gold layer.")
            return

        created_count = 0
        for row in aggregated:
            try:
                # Calculate derived values
                longs_pos = float(row.longs_pos)
                shorts_pos = float(row.shorts_pos)
                longs_margin = float(row.longs_margin)
                shorts_margin = float(row.shorts_margin)
                
                total_position = longs_pos + shorts_pos  # Net sum (shorts are negative)
                net_margin = longs_margin + shorts_margin  # Net sum (shorts are negative)

                gold_summary = GoldHyperliquidSummary(
                    timestamp=row.timestamp,
                    total_position_value_millions=total_position,
                    longs_position_value_millions=longs_pos,
                    shorts_position_value_millions=shorts_pos,
                    longs_margin_thousands=longs_margin,
                    shorts_margin_thousands=shorts_margin,
                    net_margin_thousands=net_margin,
                    position_count=row.position_count
                )
                self.db.add(gold_summary)
                created_count += 1

            except Exception as e:
                self.logger.error(f"Error creating gold summary for timestamp {row.timestamp}: {e}")

        self.logger.info(f"Created {created_count} gold summary records from {len(aggregated)} timestamps.")
