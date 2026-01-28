#!/usr/bin/env python3
# filename: deribit_btc_futures_premium.py
# Full BTC futures curve with premium & annualized % + CSV export

import requests
import time
from datetime import datetime
import pandas as pd

def get_btc_perp_price():
    url = "https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL"
    try:
        r = requests.get(url, timeout=10)
        return float(r.json()["result"]["mark_price"])
    except:
        return None

def get_futures_instruments():
    url = "https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=future&expired=false"
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
            "last_price": float(result.get("last_price", 0)) #if result.get("last_price") else None
        }
    except:
        return None

def get_data_BTC():
    print("Fetching BTC Perpetual + Futures from Deribit...\n")

    # Get spot (perpetual) price
    spot = get_btc_perp_price()
    if not spot:
        print("Failed to fetch spot price")
        return
    print(f"BTC Spot (Perpetual): ${spot:,.2f}\n")

    # Get futures
    instruments = get_futures_instruments()
    if not instruments:
        print("No futures found.")
        return

    print(f"Found {len(instruments)} futures. Fetching prices...\n")
    main = {}
    details = []
    today = datetime.now()
    today_date = datetime.now().date()
    #Active if need utc time 
    #today = datetime.now_utc.date()

    for inst in instruments:
        name = inst["instrument_name"]
        if not name.startswith("BTC-") or name.count("-") != 1:
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

    main["asset"] = "BTC"
    main["ran_at_utc"] = today
    main["source"] = "deribit"
    main["spot_price"] = spot

    
    if not details:
        print("No data fetched.")
        return
    
    return main, details