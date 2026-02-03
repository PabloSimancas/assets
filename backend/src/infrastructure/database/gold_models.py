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
    -- Directional breakdown for positions
    SUM(CASE WHEN direction = 1 THEN position_value ELSE 0 END) AS long_value,
    SUM(CASE WHEN direction = -1 THEN ABS(position_value) ELSE 0 END) AS short_value,
    -- Directional breakdown for margin
    SUM(CASE WHEN direction = 1 THEN margin_used ELSE 0 END) AS long_margin,
    SUM(CASE WHEN direction = -1 THEN margin_used ELSE 0 END) AS short_margin,
    -- Position count
    COUNT(*) AS position_count
FROM silver.hyperliquid_aggregated
GROUP BY session_timestamp, coin
ORDER BY session_timestamp DESC, ABS(SUM(position_value)) DESC;
"""

# Net position summary - same columns as hyperliquid_summary but from netted positions
GOLD_HYPERLIQUID_SUMMARY_NET = """
CREATE OR REPLACE VIEW gold.hyperliquid_summary_net_positions AS
SELECT 
    session_timestamp,
    -- Position values (millions) - computed from net positions per asset
    (SUM(long_value) + SUM(short_value)) / 1000000.0 AS total_position_value_millions,
    SUM(long_value) / 1000000.0 AS longs_position_value_millions,
    SUM(short_value) / 1000000.0 AS shorts_position_value_millions,
    -- Margin values (thousands)
    SUM(long_margin) / 1000.0 AS longs_margin_thousands,
    SUM(short_margin) / 1000.0 AS shorts_margin_thousands,
    (SUM(long_margin) + SUM(short_margin)) / 1000.0 AS net_margin_thousands,
    -- Metadata
    COUNT(*) AS position_count
FROM gold.hyperliquid_net_assets
GROUP BY session_timestamp
ORDER BY session_timestamp DESC;
"""

# All gold views to be created
GOLD_VIEWS = [
    GOLD_HYPERLIQUID_SUMMARY_VIEW,
    GOLD_HYPERLIQUID_NET_ASSETS_VIEW,
    GOLD_HYPERLIQUID_SUMMARY_NET,
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
