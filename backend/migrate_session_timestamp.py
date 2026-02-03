"""
Manual migration to add session_timestamp columns and create gold views.
Run this if the automatic migration didn't work on deployment.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.infrastructure.database.session import engine
from sqlalchemy import text

def migrate():
    print("=" * 60)
    print("MANUAL MIGRATION: Adding session_timestamp columns")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 1. Add session_timestamp to bronze.hyperliquid_positions
        print("\n1. Adding session_timestamp to bronze.hyperliquid_positions...")
        try:
            conn.execute(text("""
                ALTER TABLE bronze.hyperliquid_positions 
                ADD COLUMN IF NOT EXISTS session_timestamp TIMESTAMP
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hl_pos_session 
                ON bronze.hyperliquid_positions(vault_address, session_timestamp)
            """))
            conn.commit()
            print("   ✅ Done")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()
        
        # 2. Add session_timestamp to silver.hyperliquid_aggregated
        print("\n2. Adding session_timestamp to silver.hyperliquid_aggregated...")
        try:
            conn.execute(text("""
                ALTER TABLE silver.hyperliquid_aggregated 
                ADD COLUMN IF NOT EXISTS session_timestamp TIMESTAMP
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hl_agg_session 
                ON silver.hyperliquid_aggregated(vault_address, session_timestamp)
            """))
            conn.commit()
            print("   ✅ Done")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()
        
        # 3. Backfill existing data (optional but recommended)
        print("\n3. Backfilling session_timestamp for existing data...")
        try:
            conn.execute(text("""
                UPDATE bronze.hyperliquid_positions 
                SET session_timestamp = timestamp 
                WHERE session_timestamp IS NULL
            """))
            conn.execute(text("""
                UPDATE silver.hyperliquid_aggregated 
                SET session_timestamp = timestamp 
                WHERE session_timestamp IS NULL
            """))
            conn.commit()
            print("   ✅ Done")
        except Exception as e:
            print(f"   ⚠️  Warning: {e}")
            conn.rollback()
        
        # 4. Create/Update Gold views
        print("\n4. Creating Gold views...")
        try:
            # Summary view
            conn.execute(text("""
                CREATE OR REPLACE VIEW gold.hyperliquid_summary AS
                SELECT 
                    session_timestamp,
                    SUM(COALESCE(pos_value_millions_long, 0)) + SUM(COALESCE(pos_value_millions_short, 0)) AS total_position_value_millions,
                    SUM(COALESCE(pos_value_millions_long, 0)) AS longs_position_value_millions,
                    SUM(COALESCE(pos_value_millions_short, 0)) AS shorts_position_value_millions,
                    SUM(COALESCE(margin_thousands_long, 0)) AS longs_margin_thousands,
                    SUM(COALESCE(margin_thousands_short, 0)) AS shorts_margin_thousands,
                    SUM(COALESCE(margin_thousands_long, 0)) + SUM(COALESCE(margin_thousands_short, 0)) AS net_margin_thousands,
                    COUNT(*) AS position_count
                FROM silver.hyperliquid_aggregated
                GROUP BY session_timestamp
                ORDER BY session_timestamp DESC
            """))
            print("   ✅ hyperliquid_summary created")
            
            # Net assets view
            conn.execute(text("""
                CREATE OR REPLACE VIEW gold.hyperliquid_net_assets AS
                SELECT 
                    session_timestamp,
                    coin,
                    SUM(position_size) AS net_position_size,
                    SUM(position_value) AS net_position_value,
                    SUM(margin_used) AS total_margin_used,
                    SUM(unrealized_pnl) AS net_unrealized_pnl,
                    SUM(CASE WHEN direction = 1 THEN position_value ELSE 0 END) AS long_value,
                    SUM(CASE WHEN direction = -1 THEN ABS(position_value) ELSE 0 END) AS short_value,
                    COUNT(*) AS position_count
                FROM silver.hyperliquid_aggregated
                GROUP BY session_timestamp, coin
                ORDER BY session_timestamp DESC, ABS(net_position_value) DESC
            """))
            print("   ✅ hyperliquid_net_assets created")
            
            conn.commit()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            conn.rollback()
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)

if __name__ == "__main__":
    migrate()
