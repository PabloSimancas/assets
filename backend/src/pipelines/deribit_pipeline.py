import json
import logging
from typing import List, Dict
from datetime import datetime
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.scraping_models import WebScrape
from src.infrastructure.database.silver_models import SilverTicker
from src.infrastructure.database.models import RunMain, RunDetails, CryptoAssetSymbol, CurveShape
from sqlalchemy import desc

class DeribitPipeline:
    def __init__(self):
        self.logger = logging.getLogger("pipeline.deribit")
        self.db = SessionLocal()

    def run(self):
        self.logger.info("Starting Deribit Pipeline (Bronze -> Silver -> Gold)")
        try:
            # 1. BRONZE -> SILVER
            self._process_bronze_to_silver()
            
            # 2. SILVER -> GOLD
            self._process_silver_to_gold()
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Pipeline failed: {e}")
        finally:
            self.db.close()

    def _process_bronze_to_silver(self):
        """
        Reads unprocessed WebScrapes, parses JSON, inserts into SilverTicker.
        """
        # Get unprocessed scrapes
        scrapes = self.db.query(WebScrape).filter(
            WebScrape.processed_to_silver == False,
            WebScrape.source_identifier.like("deribit%")
        ).limit(100).all()

        if not scrapes:
            self.logger.info("No new Bronze data to process.")
            return

        ms = 0
        for scrape in scrapes:
            try:
                data = json.loads(scrape.raw_content)
                metadata = scrape.response_metadata or {}
                
                # Check type
                msg_type = metadata.get("type", "unknown")
                
                if msg_type == "spot_ticker":
                     # { "result": { "mark_price": ... } }
                     result = data.get("result", {})
                     price = float(result.get("mark_price", 0))
                     inst = metadata.get("instrument_name")
                     
                     st = SilverTicker(
                         asset_symbol=metadata.get("currency", "UNKNOWN"),
                         instrument_name=inst,
                         price=price,
                         timestamp=datetime.fromisoformat(metadata["timestamp"]),
                         source_origin="deribit"
                     )
                     self.db.add(st)
                     ms += 1
                
                elif msg_type == "future_ticker":
                     # Same structure
                     result = data.get("result", {})
                     price = float(result.get("mark_price", 0))
                     inst = metadata.get("instrument_name")
                     
                     st = SilverTicker(
                         asset_symbol=metadata.get("currency", "UNKNOWN"),
                         instrument_name=inst,
                         price=price,
                         timestamp=datetime.fromisoformat(metadata["timestamp"]),
                         source_origin="deribit"
                     )
                     self.db.add(st)
                     ms +=1

                scrape.processed_to_silver = True
            
            except Exception as e:
                self.logger.error(f"Error processing scrape {scrape.id}: {e}")
        
        self.db.flush() # Send to DB so Gold logic can query it
        self.logger.info(f"Bronze->Silver: Processed {len(scrapes)} scrapes, Created {ms} silver records.")

    def _process_silver_to_gold(self):
        """
        Aggregates latest Silver tickers to build the Gold 'RunDetails'.
        This logic mimics the original fetch_market_data.py but pulls from Silver.
        """
        # For simplicity in this demo, we'll just run for BTC and ETH
        for symbol in ["BTC", "ETH"]:
            self._generate_gold_record(symbol)

    def _generate_gold_record(self, symbol):
        # 1. Get latest Spot from Silver
        spot_record = self.db.query(SilverTicker).filter(
            SilverTicker.asset_symbol == symbol,
            SilverTicker.instrument_name.like("%-PERPETUAL")
        ).order_by(desc(SilverTicker.timestamp)).first()
        
        if not spot_record:
            return

        spot_price = spot_record.price
        
        # 2. Get latest Futures from Silver (approx same time)
        # In a real system, we'd group by 'batch_id', here we take 'recent'
        futures = self.db.query(SilverTicker).filter(
            SilverTicker.asset_symbol == symbol,
            SilverTicker.instrument_name.notlike("%-PERPETUAL"),
            SilverTicker.timestamp >= spot_record.timestamp # Very rough 'sync'
        ).limit(50).all()

        if not futures:
            return

        # Create Main Run
        run_main = RunMain(
            asset=CryptoAssetSymbol(symbol),
            source="deribit_pipeline",
            spot_price=spot_price
        )
        self.db.add(run_main)
        self.db.flush() # Get ID

        # Calculate Logic
        today_date = datetime.now().date()
        
        for f in futures:
            try:
                 # Parse Expiry from Name 'BTC-29MAR24'
                 parts = f.instrument_name.split("-")
                 if len(parts) < 2: continue
                 
                 expiry_str = parts[1]
                 expiry_date = datetime.strptime(expiry_str, "%d%b%y").date()
                 days = (expiry_date - today_date).days
                 
                 if days < 1: continue

                 premium_pct = (float(f.price) / float(spot_price) - 1) * 100
                 ann_pct = premium_pct / (days / 365.25)

                 curve = CurveShape.Contango
                 if premium_pct < -0.1: curve = CurveShape.Backwardation
                 elif premium_pct <= 0.1: curve = CurveShape.Flat

                 detail = RunDetails(
                     run_main_id=run_main.run_main_id,
                     expiry_str=expiry_date.strftime("%d %b %Y"),
                     expiry_date=expiry_date,
                     days_to_expiry=days,
                     future_price=f.price,
                     open_interest=0, # Not in SilverTicker yet
                     spot_price=spot_price,
                     premium_pct=premium_pct,
                     annualized_pct=ann_pct,
                     curve=curve,
                     instrument_name=f.instrument_name
                 )
                 self.db.add(detail)
            except Exception as e:
                self.logger.error(f"Error calc gold for {f.instrument_name}: {e}")

        self.logger.info(f"Silver->Gold: Generated Run {run_main.run_main_id} for {symbol}")
