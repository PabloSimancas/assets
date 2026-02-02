import requests
import logging
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any
from src.infrastructure.database.session import SessionLocal


class BaseScraper:
    def __init__(self, source_identifier: str, base_url: str = ""):
        self.source_identifier = source_identifier
        self.base_url = base_url
        self.logger = logging.getLogger(f"scraper.{source_identifier}")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def fetch(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Fetches a URL with basic error handling and random sleep.
        """
        try:
            # Random sleep to avoid being flagged as bot
            time.sleep(random.uniform(1.0, 3.0))
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def save_raw(self, url: str, content: str, metadata: Dict[str, Any] = None):
        """
        Saves the raw content. 
        DEPRECATED: Subclasses should implement their own saving logic to specific Bronze tables.
        This base implementation previously used WebScrape (now removed).
        """
        self.logger.warning("BaseScraper.save_raw called. No action taken as Generic WebScrape is deprecated.")

    def run(self):
        """
        Main execution method. Override this in subclasses.
        """
        raise NotImplementedError("Subclasses must implement run()")
