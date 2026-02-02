import logging
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.scrapers.hyperliquid import HyperliquidScraper
from src.pipelines.hyperliquid_pipeline import HyperliquidPipeline
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.silver_models import SilverHyperliquidPosition

def verify():
    logger.info("--- Starting Verification ---")
    
    # 1. Run Scraper
    logger.info("[1/3] Running Scraper...")
    scraper = HyperliquidScraper(vault_address="0xdfc24b077bc1425ad1dea75bcb6f8158e10df303")
    scraper.run()
    
    # 2. Run Pipeline
    logger.info("[2/3] Running Pipeline...")
    pipeline = HyperliquidPipeline()
    pipeline.run()
    
    # 3. Check DB
    logger.info("[3/3] Checking Database...")
    db = SessionLocal()
    try:
        positions = db.query(SilverHyperliquidPosition).filter(
            SilverHyperliquidPosition.vault_address == "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"
        ).all()
        
        logger.info(f"Found {len(positions)} positions in Silver layer.")
        if len(positions) > 0:
            logger.info("First 3 positions:")
            for p in positions[:3]:
                logger.info(f"- {p.coin}: Entry={p.entry_price}, Size={p.position_size}, PnL={p.unrealized_pnl}")
            
            print("\nSUCCESS: Data successfully scraped and processed to Silver layer.")
        else:
            print("\nFAILURE: No data found in Silver layer.")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify()
