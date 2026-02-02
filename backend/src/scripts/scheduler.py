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

# Setup Logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - SCHEDULER: %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database Config (Matches fetch_market_data.py)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/assets_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def job():
    logger.info("Starting scheduled job: Medallion Architecture Pipeline")
    try:
        # 1. BRONZE: Ingest Raw Data
        logger.info("Step 1: Running Scrapers (Bronze)")
        scraper = DeribitScraper(currency="BTC") # Can loop for ETH too
        scraper.run()
        
        scraper_eth = DeribitScraper(currency="ETH")
        scraper_eth.run()

        # 2. SILVER & GOLD: Process and Aggregate
        logger.info("Step 2: Running Pipelines (Silver -> Gold)")
        pipeline = DeribitPipeline()
        pipeline.run()

        logger.info("Job executed successfully.")
            
    except Exception as e:
        logger.error(f"Failed to launch job: {e}")

def check_missed_run():
    """
    Checks if we missed the 08:00 UTC run for today.
    If current time > 08:00 UTC AND no data exists for today after 08:00 UTC, run immediately.
    """
    logger.info("Checking for missed runs...")
    try:
        now_utc = datetime.now(timezone.utc)
        target_time = now_utc.replace(hour=8, minute=0, second=0, microsecond=0)

        # If we are before 8 AM UTC, we haven't missed it (scheduler will handle it)
        if now_utc < target_time:
            logger.info("Current time is before 08:00 UTC. Waiting for scheduled run.")
            return

        # If we are after 8 AM UTC, check database
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check if any run exists with ran_at_utc >= today's 8 AM
            query = text("SELECT COUNT(*) FROM crypto_forwards.run_main WHERE ran_at_utc >= :target_time")
            count = conn.execute(query, {"target_time": target_time}).scalar()
            
            if count == 0:
                logger.warning(f"Missed scheduled run for {target_time.date()}. Running immediately...")
                job()
            else:
                logger.info("Data for today already exists. No Catch-up needed.")
                
    except Exception as e:
        logger.error(f"Error checking missed run: {e}")

# Schedule the job
# Note: In container, time is usually UTC
# Schedule the job
# Note: In container, time is usually UTC
schedule.every().day.at("08:00").do(job)

logger.info("Scheduler started.")

# Check for missed run on startup
check_missed_run()

logger.info("Waiting for next job at 08:00 UTC...")

# Loop
while True:
    schedule.run_pending()
    time.sleep(60)
