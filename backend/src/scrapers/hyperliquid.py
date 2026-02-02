from typing import Dict, Any
from src.scrapers.base import BaseScraper
from datetime import datetime
import json
import time

class HyperliquidScraper(BaseScraper):
    def __init__(self, vault_address: str):
        # identifier unique to this vault
        super().__init__(
            source_identifier=f"hyperliquid_vault_{vault_address}",
            base_url="https://api.hyperliquid.xyz"
        )
        self.vault_address = vault_address

    def run(self):
        self.logger.info(f"Starting Hyperliquid Scraper for Vault: {self.vault_address}")
        
        # 1. Fetch Vault Details (Parent)
        endpoint = "/info"
        url = self.base_url + endpoint
        
        payload = {
            "type": "vaultDetails",
            "vaultAddress": self.vault_address
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            vault_data_text = response.text
            metadata = {
                "type": "vault_details",
                "vault_address": self.vault_address,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code
            }
            
            # Save parent data
            self.save_raw(
                url=url,
                content=vault_data_text,
                metadata=metadata
            )
            self.logger.info("Successfully scraped Hyperliquid vault details")
            
            # 2. Parse for Child Addresses
            try:
                data = json.loads(vault_data_text)
                # Structure: relationship -> data -> childAddresses
                relationship = data.get("relationship", {})
                rel_data = relationship.get("data", {})
                child_addresses = rel_data.get("childAddresses", [])
                
                if not child_addresses:
                    self.logger.info("No child addresses found in vault details.")
                else:
                    self.logger.info(f"Found {len(child_addresses)} child addresses. Scraping positions for each.")
                    
                    for child_addr in child_addresses:
                        self._scrape_child_positions(child_addr)
                        time.sleep(0.5) # Rate limit politeness

            except json.JSONDecodeError:
                self.logger.error("Failed to parse vault details JSON for child discovery.")
            except Exception as e:
                self.logger.error(f"Error extracting child addresses: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Hyperliquid vault: {e}")

    def _scrape_child_positions(self, user_address: str):
        """Helper to scrape clearinghouse state for a specific child address."""
        url = self.base_url + "/info"
        payload = {
            "type": "clearinghouseState",
            "user": user_address
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            metadata = {
                "type": "child_clearinghouse_state",
                "parent_vault": self.vault_address,
                "user_address": user_address,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code
            }
            
            # We use a unique source identifier suffix for children effectively? 
            # Actually save_raw uses self.source_identifier which is the PARENT vault ID.
            # This is fine, we can filter by metadata 'type' in the pipeline.
            self.save_raw(
                url=url + f"?user={user_address}", # distinct logical URL
                content=response.text,
                metadata=metadata
            )
            self.logger.info(f"Scraped positions for child {user_address}")
            
        except Exception as e:
            self.logger.error(f"Failed to scrape child {user_address}: {e}")

    def save_raw(self, url: str, content: str, metadata: Dict[str, Any] = None):
        """
        Overrides BaseScraper.save_raw to save to HyperliquidVault table in a separate schema.
        """
        from src.infrastructure.database.session import SessionLocal
        from src.infrastructure.database.scraping_models import HyperliquidVault
        
        db = SessionLocal()
        try:
            # metadata contains 'vault_address' usually, but use self.vault_address to be safe
            vault_addr = self.vault_address
            
            scrape = HyperliquidVault(
                vault_address=vault_addr,
                url=url,
                raw_content=content,
                response_metadata=metadata,
                processed_to_silver=False
            )
            db.add(scrape)
            db.commit()
            self.logger.info(f"Saved raw data for {url} to hyperliquid_vaults.raw_vaults")
        except Exception as e:
            self.logger.error(f"Database error saving raw scrape: {e}")
            db.rollback()
        finally:
            db.close()
