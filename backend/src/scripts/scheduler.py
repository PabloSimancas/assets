import time
import schedule
import subprocess
import logging
import sys
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from src.scrapers.deribit import DeribitScraper
from src.pipelines.deribit_pipeline import DeribitPipeline
from src.scrapers.hyperliquid import HyperliquidScraper
from src.pipelines.hyperliquid_pipeline import HyperliquidPipeline

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
    logger.info("Starting Daily Job: Deribit Pipeline")
    try:
        # 1. BRONZE: Ingest Raw Data
        logger.info("Step 1: Running Deribit Scrapers (Bronze)")
        scraper = DeribitScraper(currency="BTC")
        scraper.run()
        
        scraper_eth = DeribitScraper(currency="ETH")
        scraper_eth.run()

        # 2. SILVER & GOLD: Process
        logger.info("Step 2: Running Deribit Pipeline (Silver -> Gold)")
        pipeline = DeribitPipeline()
        pipeline.run()
        
        logger.info("Daily Deribit Job executed successfully.")
    except Exception as e:
        logger.error(f"Failed to run daily Deribit job: {e}")

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

        logger.info("Hourly Hyperliquid Job executed successfully.")
    except Exception as e:
        logger.error(f"Failed to run hourly Hyperliquid job: {e}")

def check_missed_run():
    """
    Checks if we missed the 08:00 UTC run for Deribit.
    """
    logger.info("Checking for missed daily runs...")
    try:
        now_utc = datetime.now(timezone.utc)
        target_time = now_utc.replace(hour=8, minute=0, second=0, microsecond=0)

        if now_utc < target_time:
            logger.info("Current time is before 08:00 UTC. Waiting for scheduled run.")
            return

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM crypto_forwards.run_main WHERE ran_at_utc >= :target_time")
            count = conn.execute(query, {"target_time": target_time}).scalar()
            
            if count == 0:
                logger.warning(f"Missed scheduled run for {target_time.date()}. Running Deribit immediately...")
                run_daily_deribit()
            else:
                logger.info("Deribit data for today already exists.")
                
    except Exception as e:
        logger.error(f"Error checking missed run: {e}")

# Ensure schema exists on scheduler start (idempotent)
try:
    from src.infrastructure.database.session import Base
    from src.infrastructure.database.scraping_models import HyperliquidVault
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    logger.info("Ensured DB schemas exist.")
except Exception as e:
    logger.error(f"Failed to ensure DB schemas: {e}")

# Schedule the jobs
schedule.every().day.at("08:00").do(run_daily_deribit)
schedule.every().hour.do(run_hourly_hyperliquid)

logger.info("Scheduler started.")

# Check for missed run on startup
check_missed_run()

# Run Hyperliquid immediately on startup (per user request)
logger.info("Triggering initial Hyperliquid run...")
run_hourly_hyperliquid()

logger.info("Waiting for scheduled jobs...")

while True:
    schedule.run_pending()
    sys.stdout.flush()
    time.sleep(60)
