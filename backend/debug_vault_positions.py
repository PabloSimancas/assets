import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_positions")

def get_clearinghouse_state(address):
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "clearinghouseState",
        "user": address
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching clearinghouse state: {e}")
        return None

if __name__ == "__main__":
    # Child addresses known to hold positions
    addresses = [
        "0x010461c14e146ac35fe42271bdc1134ee31c703a",
        "0x31ca8395cf837de08b24da3f660e77761dfb974b"
    ]
    
    first_position_dumped = False

    for addr in addresses:
        print(f"\nProcessing Address: {addr}")
        data = get_clearinghouse_state(addr)
        
        if data and "assetPositions" in data:
            positions = data["assetPositions"]
            print(f"Found {len(positions)} positions.")
            
            # Print raw margin summary if available
            if "marginSummary" in data:
                print(f"Margin Summary: {json.dumps(data['marginSummary'], indent=2)}")

            for i, item in enumerate(positions):
                pos = item.get("position", {})
                
                # Filter out empty positions
                size = float(pos.get("szi", "0"))
                if size == 0:
                    continue

                # DUMP RAW JSON for the very first valid position to see ALL available columns
                if not first_position_dumped:
                    print("\n--- [DEBUG] RAW POSITION OBJECT (First found) ---")
                    print(json.dumps(pos, indent=2))
                    print("--- [DEBUG] END RAW POSITION OBJECT ---\n")
                    first_position_dumped = True

                # Extract standard fields
                coin = pos.get("coin", "N/A")
                entry_px = pos.get("entryPx", "0")
                pnl = pos.get("unrealizedPnl", "0")
                liquidation_px = pos.get("liquidationPx", "N/A")
                
                # Check for Margin/Leverage keys
                leverage_info = pos.get("leverage", {})
                leverage_type = leverage_info.get("type", "cross")
                leverage_val = leverage_info.get("value", "N/A")
                
                margin_used = pos.get("marginUsed", "N/A")
                max_leverage = pos.get("maxLeverage", "N/A")
                cum_funding = pos.get("cumFunding", "N/A") 
                position_value = pos.get("positionValue", "N/A")

                print(f"Position: {coin}")
                print(f"  Size: {size}")
                print(f"  Entry Price: {entry_px}")
                print(f"  Position Value: {position_value}")
                print(f"  Unrealized PnL: {pnl}")
                print(f"  Liquidation Px: {liquidation_px}")
                print(f"  Leverage: {leverage_type} ({leverage_val}x)")
                print(f"  Margin Used: {margin_used}")
                print(f"  Cum. Funding: {cum_funding}") # Might be None
                print("-" * 30)

        else:
             print("No positions found.")
