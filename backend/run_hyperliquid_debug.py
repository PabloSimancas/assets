
import logging
import sys
import os
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

from src.scrapers.hyperliquid import HyperliquidScraper
from src.pipelines.hyperliquid_pipeline import HyperliquidPipeline
from src.infrastructure.database.session import SessionLocal, Base
from src.infrastructure.database.scraping_models import HyperliquidVault
from src.infrastructure.database.silver_models import SilverHyperliquidPosition

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_pipeline")

def test_pipeline():
    logger.info("--- Testing Hyperliquid Pipeline ---")
    
    # 1. Ensure Schema
    logger.info("Ensuring schemas exist...")
    # This assumes DATABASE_URL is set in env or defaults correctly
    from src.infrastructure.database.session import engine
    
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS hyperliquid_vaults;"))
            conn.commit()
        
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Failed to ensure schema (are you connected to DB?): {e}")
        return

    # 2. Count before
    db = SessionLocal()
    try:
        count_bronze_before = db.query(HyperliquidVault).count()
        count_silver_before = db.query(SilverHyperliquidPosition).count()
    except Exception as e:
        logger.error(f"Failed to query DB: {e}")
        return
    db.close()
    
    logger.info(f"Bronze before: {count_bronze_before}, Silver before: {count_silver_before}")

    # 3. Run Scraper
    logger.info("Running Scraper...")
    try:
        scraper = HyperliquidScraper(vault_address="0xdfc24b077bc1425ad1dea75bcb6f8158e10df303")
        scraper.run()
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return
    
    # 4. Run Pipeline
    logger.info("Running Pipeline...")
    try:
        pipeline = HyperliquidPipeline()
        pipeline.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return
    
    # 5. Verify
    db = SessionLocal()
    count_bronze_after = db.query(HyperliquidVault).count()
    count_silver_after = db.query(SilverHyperliquidPosition).count()
    
    logger.info(f"Bronze after: {count_bronze_after} (+{count_bronze_after - count_bronze_before})")
    logger.info(f"Silver after: {count_silver_after} (+{count_silver_after - count_silver_before})")
    
    new_items = db.query(SilverHyperliquidPosition).order_by(SilverHyperliquidPosition.id.desc()).limit(5).all()
    if new_items:
        logger.info("Sample Silver Data:")
        for item in new_items:
            logger.info(f"Time: {item.timestamp}, Coin: {item.coin}, Size: {item.position_size}, Val: {item.position_value}")
    else:
        logger.warning("No silver items found.")

    db.close()

if __name__ == "__main__":
    test_pipeline()
