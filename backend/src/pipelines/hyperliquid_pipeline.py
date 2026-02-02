import json
import logging
from typing import List, Dict
from datetime import datetime
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.scraping_models import HyperliquidVault
from src.infrastructure.database.silver_models import SilverHyperliquidPosition

class HyperliquidPipeline:
    def __init__(self):
        self.logger = logging.getLogger("pipeline.hyperliquid")
        self.db = SessionLocal()

    def run(self):
        self.logger.info("Starting Hyperliquid Pipeline (Bronze -> Silver)")
        try:
            self._process_bronze_to_silver()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Pipeline failed: {e}")
        finally:
            self.db.close()

    def _process_bronze_to_silver(self):
        """
        Reads unprocessed HyperliquidVault items, parses JSON, inserts into SilverHyperliquidPosition.
        """
        # Get unprocessed scrapes
        scrapes = self.db.query(HyperliquidVault).filter(
            HyperliquidVault.processed_to_silver == False
        ).limit(50).all()

        if not scrapes:
            self.logger.info("No new Hyperliquid data to process.")
            return

        ms = 0
        for scrape in scrapes:
            try:
                data = json.loads(scrape.raw_content)
                metadata = scrape.response_metadata or {}
                timestamp = datetime.fromisoformat(metadata["timestamp"])
                
                scrape_type = metadata.get("type", "unknown")
                vault_addr = metadata.get("vault_address") or metadata.get("parent_vault") or "unknown"
                user_addr = metadata.get("user_address") # Child address

                # We primarily want to process position data from 'child_clearinghouse_state'
                # But 'vault_details' might be useful later. For now, only extract positions if present.
                
                positions = []
                if "assetPositions" in data:
                    positions = data["assetPositions"]
                elif "portfolio" in data and "assetPositions" in data["portfolio"]:
                     # Fallback for vaultDetails if it ever has positions directly
                    positions = data["portfolio"]["assetPositions"]
                
                if not positions:
                    # Mark as processed even if no positions, to avoid re-processing loop
                    scrape.processed_to_silver = True
                    continue

                for pos_wrapper in positions:
                    # Structure: { "position": { "coin": "BTC", ... } }
                    pos = pos_wrapper.get("position", {})
                    if not pos:
                        continue
                        
                    coin = pos.get("coin")
                    entry = pos.get("entryPx")
                    szi = pos.get("szi")
                    unrealized = pos.get("unrealizedPnl")
                    margin = pos.get("marginUsed")
                    liq_px = pos.get("liquidationPx")
                    roe = pos.get("returnOnEquity")
                    max_lev = pos.get("maxLeverage")
                    
                    # Leverage
                    leverage_info = pos.get("leverage", {})
                    lev_type = leverage_info.get("type")
                    lev_val = leverage_info.get("value")
                    
                    # Funding
                    cum_funding = pos.get("cumFunding", {})
                    cf_all = cum_funding.get("allTime")
                    cf_open = cum_funding.get("sinceOpen")
                    cf_chg = cum_funding.get("sinceChange")

                    silver_pos = SilverHyperliquidPosition(
                        vault_address=vault_addr,
                        user_address=user_addr,
                        coin=coin,
                        entry_price=float(entry) if entry else 0,
                        mark_price=float(pos.get("positionValue", 0)) / abs(float(szi)) if szi and float(szi) != 0 else 0,
                        position_size=float(szi) if szi else 0,
                        # position_value not explicitly in raw sometimes? 
                        # positions_detailed.txt shows "positionValue": "1289273.3020200001"
                        position_value=float(pos.get("positionValue", 0)),
                        margin_used=float(margin) if margin else 0,
                        unrealized_pnl=float(unrealized) if unrealized else 0,
                        return_on_equity=float(roe) if roe else 0,
                        liquidation_px=float(liq_px) if liq_px else None,
                        max_leverage=int(max_lev) if max_lev else None,
                        
                        leverage_type=lev_type,
                        leverage_value=int(lev_val) if lev_val else None,
                        
                        cum_funding_all_time=float(cf_all) if cf_all else 0,
                        cum_funding_since_open=float(cf_open) if cf_open else 0,
                        cum_funding_since_change=float(cf_chg) if cf_chg else 0,

                        timestamp=timestamp,
                        source_origin="hyperliquid"
                    )
                    self.db.add(silver_pos)
                    ms += 1

                scrape.processed_to_silver = True
            
            except Exception as e:
                self.logger.error(f"Error processing scrape {scrape.id}: {e}")
        
        self.logger.info(f"Hyperliquid Processed {len(scrapes)} scrapes, Created {ms} silver records.")
