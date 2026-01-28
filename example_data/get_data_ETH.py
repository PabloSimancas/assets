#!/usr/bin/env python3
# filename: deribit_eth_futures_premium.py
# ETH futures curve with premium & annualized % + CSV export

import requests
import time
from datetime import datetime
import pandas as pd

def get_eth_perp_price():
    url = "https://www.deribit.com/api/v2/public/ticker?instrument_name=ETH-PERPETUAL"
    try:
        r = requests.get(url, timeout=10)
        return float(r.json()["result"]["mark_price"])
    except:
        return None

def get_eth_futures():
    url = "https://www.deribit.com/api/v2/public/get_instruments?currency=ETH&kind=future&expired=false"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("result", [])
    except Exception as e:
        print(f"Error fetching instruments: {e}")
        return []

def get_ticker_data(instrument_name):
    url = f"https://www.deribit.com/api/v2/public/ticker?instrument_name={instrument_name}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        result = r.json().get("result", {})
        return {
            "mark_price": float(result.get("mark_price", 0)),
            "open_interest": int(result.get("open_interest", 0)),
            "volume_24h": float(result.get("volume", 0)),
            "last_price": float(result.get("last_price", 0)) if result.get("last_price") else None
        }
    except:
        return None

def get_data_ETH():
    print("Fetching ETH Perpetual + Futures from Deribit...\n")

    spot = get_eth_perp_price()
    if not spot:
        print("Failed to fetch ETH spot price")
        return
    print(f"ETH Spot (Perpetual): ${spot:,.2f}\n")

    instruments = get_eth_futures()
    if not instruments:
        print("No ETH futures found.")
        return

    print(f"Found {len(instruments)} ETH futures. Fetching prices...\n")

    main = {}
    details = []
    today = datetime.now()
    today_date = datetime.now().date()

    for inst in instruments:
        name = inst["instrument_name"]
        if not name.startswith("ETH-") or name.count("-") != 1:
            continue
        if name.endswith("-PERPETUAL"):
            continue

        try:
            expiry_str = name.split("-")[1]
            expiry = datetime.strptime(expiry_str, "%d%b%y").date()
            days = (expiry - today_date).days
            if days < 1:
                continue

            print(f"Fetching {name}...")
            ticker = get_ticker_data(name)
            if not ticker or ticker["mark_price"] == 0:
                continue

            fwd = ticker["mark_price"]
            premium_pct = (fwd / spot - 1) * 100
            ann_pct = premium_pct / (days / 365.25)

            details.append((
                #"Expiry_str":
                expiry.strftime("%d %b %Y"),
                #"Expiry_date": 
                expiry,
                #"Days":
                days,
                #"Futures $": 
                fwd,
                #"OI":
                ticker['open_interest'],
                #"Spot $":         
                spot,
                #"Premium %":      
                premium_pct,
                #"Annualized %":   
                ann_pct,
                #"Curve":          
                "Contango" if premium_pct > 1 else "Backwardation" if premium_pct < -1 else "Flat",
                name
            ))
            time.sleep(0.05)
        except Exception as e:
            print(f"Error on {name}: {e}")

    main["asset"] = "ETH"
    main["ran_at_utc"] = today
    main["source"] = "deribit"
    main["spot_price"] = spot

    if not details:
        print("No data fetched.")
        return
    
    return main, details

