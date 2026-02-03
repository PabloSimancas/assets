"""
Gold Layer Views for Hyperliquid

SQL View definitions that aggregate silver layer data on the fly.
Views are created/updated during scheduler startup.
"""

# View definitions as raw SQL
GOLD_HYPERLIQUID_SUMMARY_VIEW = """
CREATE OR REPLACE VIEW gold.hyperliquid_summary AS
SELECT 
    session_timestamp,
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
GROUP BY session_timestamp
ORDER BY session_timestamp DESC;
"""

# Net asset positions per session
GOLD_HYPERLIQUID_NET_ASSETS_VIEW = """
CREATE OR REPLACE VIEW gold.hyperliquid_net_assets AS
SELECT 
    session_timestamp,
    coin,
    -- Net position calculations
    SUM(position_size) AS net_position_size,
    SUM(position_value) AS net_position_value,
    SUM(margin_used) AS total_margin_used,
    SUM(unrealized_pnl) AS net_unrealized_pnl,
    -- Directional breakdown
    SUM(CASE WHEN direction = 1 THEN position_value ELSE 0 END) AS long_value,
    SUM(CASE WHEN direction = -1 THEN ABS(position_value) ELSE 0 END) AS short_value,
    -- Position count
    COUNT(*) AS position_count
FROM silver.hyperliquid_aggregated
GROUP BY session_timestamp, coin
ORDER BY session_timestamp DESC, ABS(SUM(position_value)) DESC;
"""

# All gold views to be created
GOLD_VIEWS = [
    GOLD_HYPERLIQUID_SUMMARY_VIEW,
    GOLD_HYPERLIQUID_NET_ASSETS_VIEW,
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
