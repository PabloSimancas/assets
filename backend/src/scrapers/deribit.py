import json
import time
from src.scrapers.base import BaseScraper
from datetime import datetime

class DeribitScraper(BaseScraper):
    def __init__(self, currency: str = "BTC"):
        super().__init__(source_identifier=f"deribit_{currency.lower()}", base_url="https://www.deribit.com/api/v2")
        self.currency = currency

    def run(self):
        self.logger.info(f"Starting Deribit Scraper for {self.currency}")
        
        # 1. Fetch Spot Price
        # instrument_name = BTC-PERPETUAL
        self._scrape_ticker(f"{self.currency}-PERPETUAL", is_spot=True)

        # 2. Fetch Instruments List
        instruments = self._scrape_instruments()
        
        if not instruments:
            return

        # 3. Fetch Ticker for each valid future
        # Filter logic from original script to avoid spamming useless tickers
        targets = []
        today_date = datetime.now().date()

        for inst in instruments:
            name = inst["instrument_name"]
            # Filter: Must be {SYMBOL}-DDMMMYY
            if not name.startswith(f"{self.currency}-") or name.count("-") != 1:
                continue
            if name.endswith("-PERPETUAL"):
                continue
            
            # Simple expiry check (optional, but saves bandwidth)
            try:
                expiry_str = name.split("-")[1]
                expiry = datetime.strptime(expiry_str, "%d%b%y").date()
                if (expiry - today_date).days < 1:
                    continue
                targets.append(name)
            except:
                continue

        self.logger.info(f"Fetching tickers for {len(targets)} instruments...")
        for name in targets:
            self._scrape_ticker(name)
            
    def _scrape_instruments(self):
        endpoint = "/public/get_instruments"
        params = {
            "currency": self.currency,
            "kind": "future",
            "expired": "false"
        }
        url = self.base_url + endpoint
        response = self.fetch(url, params=params)
        
        if response:
            metadata = {
                "type": "instruments_list",
                "currency": self.currency,
                "timestamp": datetime.utcnow().isoformat()
            }
            # Save raw
            self.save_raw(response.url, response.text, metadata)
            
            try:
                return response.json().get("result", [])
            except:
                return []
        return []

    def _scrape_ticker(self, instrument_name, is_spot=False):
        endpoint = "/public/ticker"
        params = {"instrument_name": instrument_name}
        url = self.base_url + endpoint
        
        response = self.fetch(url, params=params)
        if response:
             metadata = {
                "type": "spot_ticker" if is_spot else "future_ticker",
                "instrument_name": instrument_name,
                "currency": self.currency,
                "timestamp": datetime.utcnow().isoformat()
            }
             self.save_raw(response.url, response.text, metadata)
