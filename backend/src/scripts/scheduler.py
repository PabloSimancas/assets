import time
import schedule
import subprocess
import logging
import sys
import os
# Add project root to sys.path to allow imports from src
# Script is in src/scripts/scheduler.py, so we need to go up 2 levels (src, then root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
# from src.scrapers.deribit import DeribitScraper
# from src.pipelines.deribit_pipeline import DeribitPipeline
from src.scrapers.hyperliquid import HyperliquidScraper
from src.pipelines.hyperliquid_pipeline import HyperliquidPipeline
from src.pipelines.hyperliquid_aggregated_pipeline import HyperliquidAggregatedPipeline

# Setup Logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - SCHEDULER: %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database Config (Matches fetch_market_data.py)
# Database Config (Matches fetch_market_data.py)
try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError:
    logger.critical("DATABASE_URL environment variable is NOT set. Scheduler cannot run.")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def run_daily_deribit():
    logger.info("Starting Daily Job: Deribit Pipeline - DISABLED (Legacy models removed)")
    # try:
    #     # 1. BRONZE: Ingest Raw Data
    #     logger.info("Step 1: Running Deribit Scrapers (Bronze)")
    #     scraper = DeribitScraper(currency="BTC")
    #     scraper.run()
    #     
    #     scraper_eth = DeribitScraper(currency="ETH")
    #     scraper_eth.run()
    #
    #     # 2. SILVER & GOLD: Process
    #     logger.info("Step 2: Running Deribit Pipeline (Silver -> Gold)")
    #     pipeline = DeribitPipeline()
    #     pipeline.run()
    #     
    #     logger.info("Daily Deribit Job executed successfully.")
    # except Exception as e:
    #     logger.error(f"Failed to run daily Deribit job: {e}")
    pass

def run_hourly_hyperliquid():
    logger.info("Starting Hourly Job: Hyperliquid Pipeline")
    try:
        # Hyperliquid Vault
        logger.info("Step 1: Running Hyperliquid Scraper")
        # Ensure schema exists (lightweight check or rely on startup)
        
        hl_scraper = HyperliquidScraper(vault_address="0xdfc24b077bc1425ad1dea75bcb6f8158e10df303")
        hl_scraper.run() # This now saves to bronze.raw_vaults schema

        # Silver/Gold Pipeline
        logger.info("Step 2: Running Hyperliquid Pipeline")
        hl_pipeline = HyperliquidPipeline()
        hl_pipeline.run()

        # Step 3: Aggregated Pipeline (calculates direction & scaled values)
        logger.info("Step 3: Running Hyperliquid Aggregated Pipeline")
        agg_pipeline = HyperliquidAggregatedPipeline()
        agg_pipeline.run()

        # Gold layer is a VIEW - no pipeline needed, auto-updates from silver

        logger.info("Hourly Hyperliquid Job executed successfully.")
    except Exception as e:
        logger.error(f"Failed to run hourly Hyperliquid job: {e}")

def check_missed_run():
    """
    Checks if we missed the 08:00 UTC run for Deribit.
    """
    logger.info("Checking for missed daily runs... (Deribit Disabled)")
    pass

def should_run_hyperliquid_on_startup():
    """
    Checks if Hyperliquid was run recently (within the last 55 minutes).
    Returns True if we should run, False if recent data already exists.
    This prevents duplicate runs when container restarts near the hour mark.
    """
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check if any bronze data was scraped in the last 55 minutes
            query = text("""
                SELECT COUNT(*) FROM bronze.hyperliquid_vaults 
                WHERE scraped_at >= NOW() - INTERVAL '55 minutes'
            """)
            count = conn.execute(query).scalar()
            
            if count > 0:
                logger.info(f"Found {count} Hyperliquid scrapes in the last 55 minutes. Skipping startup run.")
                return False
            else:
                logger.info("No recent Hyperliquid data found. Will run on startup.")
                return True
    except Exception as e:
        logger.warning(f"Could not check for recent Hyperliquid runs: {e}. Running anyway.")
        return True

# Ensure schema exists on scheduler start (idempotent)
if __name__ == "__main__":
    # Ensure schema exists on scheduler start (idempotent)
    try:
        from src.infrastructure.database.session import Base
        from src.infrastructure.database.scraping_models import HyperliquidVault
        from src.infrastructure.database.silver_models import SilverHyperliquidPosition, SilverHyperliquidAggregated
        from src.infrastructure.database.gold_models import create_gold_views
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
            conn.commit()
        Base.metadata.create_all(bind=engine)
        # Create gold views (no tables for gold layer, only views)
        create_gold_views(engine)
        logger.info("Ensured DB schemas and gold views exist.")
    except Exception as e:
        logger.error(f"Failed to ensure DB schemas: {e}")

    # Schedule the jobs
    # schedule.every().day.at("08:00").do(run_daily_deribit)
    schedule.every().hour.do(run_hourly_hyperliquid)

    logger.info("Scheduler started.")

    # Check for missed run on startup
    check_missed_run()

    # Run Hyperliquid on startup ONLY if no recent data exists (prevents duplicates)
    if should_run_hyperliquid_on_startup():
        logger.info("Triggering initial Hyperliquid run...")
        run_hourly_hyperliquid()
    else:
        logger.info("Skipping initial Hyperliquid run (recent data exists).")

    logger.info("Waiting for scheduled jobs...")

    while True:
        schedule.run_pending()
        sys.stdout.flush()
        time.sleep(60)
