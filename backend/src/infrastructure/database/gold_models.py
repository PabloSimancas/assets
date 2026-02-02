"""
Gold Layer Views for Hyperliquid

SQL View definitions that aggregate silver layer data on the fly.
Views are created/updated during scheduler startup.
"""

# View definitions as raw SQL
GOLD_HYPERLIQUID_SUMMARY_VIEW = """
CREATE OR REPLACE VIEW gold.hyperliquid_summary AS
SELECT 
    timestamp,
    -- Position values (millions) - net sum since shorts are negative
    SUM(COALESCE(pos_value_millions_long, 0)) + SUM(COALESCE(pos_value_millions_short, 0)) AS total_position_value_millions,
    SUM(COALESCE(pos_value_millions_long, 0)) AS longs_position_value_millions,
    SUM(COALESCE(pos_value_millions_short, 0)) AS shorts_position_value_millions,
    -- Margin values (thousands)
    SUM(COALESCE(margin_thousands_long, 0)) AS longs_margin_thousands,
    SUM(COALESCE(margin_thousands_short, 0)) AS shorts_margin_thousands,
    SUM(COALESCE(margin_thousands_long, 0)) + SUM(COALESCE(margin_thousands_short, 0)) AS net_margin_thousands,
    -- Metadata
    COUNT(*) AS position_count
FROM silver.hyperliquid_aggregated
GROUP BY timestamp
ORDER BY timestamp DESC;
"""

# All gold views to be created
GOLD_VIEWS = [
    GOLD_HYPERLIQUID_SUMMARY_VIEW,
]


def create_gold_views(engine):
    """
    Creates all gold layer views. Safe to run multiple times 
    (CREATE OR REPLACE handles idempotency).
    """
    from sqlalchemy import text
    import logging
    
    logger = logging.getLogger("gold_views")
    
    with engine.connect() as conn:
        for view_sql in GOLD_VIEWS:
            try:
                conn.execute(text(view_sql))
                conn.commit()
                logger.info("Gold views created/updated successfully.")
            except Exception as e:
                logger.error(f"Failed to create gold view: {e}")
                raise
