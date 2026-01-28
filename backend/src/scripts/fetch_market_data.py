import requests
import time
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# Setup Logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/fetch_market.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/assets_db")
engine = create_engine(DATABASE_URL)

def get_perp_price(symbol):
    # Deribit uses BTC-PERPETUAL / ETH-PERPETUAL
    instrument = f"{symbol}-PERPETUAL"
    url = f"https://www.deribit.com/api/v2/public/ticker?instrument_name={instrument}"
    try:
        r = requests.get(url, timeout=10)
        return float(r.json()["result"]["mark_price"])
    except Exception as e:
        logger.error(f"Error fetching spot for {symbol}: {e}")
        return None

def get_futures_instruments(currency):
    url = f"https://www.deribit.com/api/v2/public/get_instruments?currency={currency}&kind=future&expired=false"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("result", [])
    except Exception as e:
        logger.error(f"Error fetching instruments for {currency}: {e}")
        return []

def get_ticker_data(instrument_name):
    url = f"https://www.deribit.com/api/v2/public/ticker?instrument_name={instrument_name}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        result = r.json().get("result", {})
        return {
            "mark_price": float(result.get("mark_price", 0)),
            "open_interest": float(result.get("open_interest", 0)),
        }
    except Exception as e:
        logger.error(f"Error fetching ticker for {instrument_name}: {e}")
        return None

def process_asset(symbol):
    logger.info(f"Starting process for {symbol}")
    
    # 1. Get Spot Price
    spot = get_perp_price(symbol)
    if not spot:
        logger.warning(f"Aborting {symbol}: Could not get spot price.")
        return

    # 2. Get Instruments
    instruments = get_futures_instruments(symbol)
    if not instruments:
        logger.warning(f"Aborting {symbol}: No instruments found.")
        return

    logger.info(f"Found {len(instruments)} futures for {symbol}. Fetching details...")

    # 3. Filter and Process
    valid_data = []
    today_date = datetime.now().date()

    for inst in instruments:
        name = inst["instrument_name"]
        # Filter logic: Must be {SYMBOL}-DDMMMYY
        if not name.startswith(f"{symbol}-") or name.count("-") != 1:
            continue
        if name.endswith("-PERPETUAL"):
            continue

        try:
            expiry_str = name.split("-")[1]
            expiry = datetime.strptime(expiry_str, "%d%b%y").date()
            days = (expiry - today_date).days
            
            if days < 1:
                continue

            ticker = get_ticker_data(name)
            if not ticker or ticker["mark_price"] == 0:
                continue

            fwd_price = ticker["mark_price"]
            premium_pct = (fwd_price / spot - 1) * 100
            ann_pct = premium_pct / (days / 365.25) if days > 0 else 0
            
            curve_shape = "Contango"
            if premium_pct < -0.1: # Tolerance
                curve_shape = "Backwardation"
            elif -0.1 <= premium_pct <= 0.1:
                curve_shape = "Flat"

            valid_data.append({
                "expiry_str": expiry.strftime("%d %b %Y"),
                "expiry_date": expiry,
                "days_to_expiry": days,
                "future_price": fwd_price,
                "open_interest": ticker["open_interest"],
                "spot_price": spot,
                "premium_pct": premium_pct,
                "annualized_pct": ann_pct,
                "curve": curve_shape,
                "instrument_name": name
            })
            time.sleep(0.05) # Rate limit kindness

        except Exception as e:
            logger.error(f"Error processing {name}: {e}")

    if not valid_data:
        logger.info(f"No valid future data collected for {symbol}.")
        return

    # 4. Save to DB
    save_to_db(symbol, spot, valid_data)
    logger.info(f"Successfully processed {len(valid_data)} records for {symbol}.")

def save_to_db(symbol, spot, data):
    try:
        with engine.begin() as conn:
            # Insert Main Run
            result = conn.execute(
                text("""
                    INSERT INTO crypto_forwards.run_main (asset, spot_price)
                    VALUES (:asset, :spot)
                    RETURNING run_main_id
                """),
                {"asset": symbol, "spot": spot}
            )
            run_id = result.scalar()

            # Insert Details
            for row in data:
                conn.execute(
                    text("""
                        INSERT INTO crypto_forwards.run_details 
                        (run_main_id, expiry_str, expiry_date, days_to_expiry, future_price, open_interest, spot_price, premium_pct, annualized_pct, curve, instrument_name)
                        VALUES (:run_id, :expiry_str, :expiry_date, :days, :fwd, :oi, :spot, :prem, :ann, :curve, :inst)
                    """),
                    {
                        "run_id": run_id,
                        "expiry_str": row["expiry_str"],
                        "expiry_date": row["expiry_date"],
                        "days": row["days_to_expiry"],
                        "fwd": row["future_price"],
                        "oi": row["open_interest"],
                        "spot": row["spot_price"],
                        "prem": row["premium_pct"],
                        "ann": row["annualized_pct"],
                        "curve": str(row["curve"]),
                        "inst": row["instrument_name"]
                    }
                )
    except Exception as e:
        logger.error(f"Database Error for {symbol}: {e}")
        raise

def main():
    logger.info("Starting Daily Market Data Fetch Job")
    process_asset('BTC')
    process_asset('ETH')
    logger.info("Job Complete")

if __name__ == "__main__":
    main()
