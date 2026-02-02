from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.infrastructure.database.session import get_db

router = APIRouter(
    prefix="/debug",
    tags=["debug"]
)

@router.get("/status")
async def debug_status(db: Session = Depends(get_db)):
    results = {}
    
    try:
        # Check current search path
        search_path = db.execute(text("SHOW search_path")).scalar()
        results["search_path"] = search_path
        
        # Check current schema
        current_schema = db.execute(text("SELECT current_schema()")).scalar()
        results["current_schema"] = current_schema
        
        # Count public.assets
        try:
            count_public = db.execute(text("SELECT COUNT(*) FROM public.assets")).scalar()
            results["count_public_assets"] = count_public
        except Exception as e:
            results["count_public_assets_error"] = str(e)

        # Count default assets
        try:
            count_assets = db.execute(text("SELECT COUNT(*) FROM assets")).scalar()
            results["count_assets_default"] = count_assets
        except Exception as e:
            results["count_assets_default_error"] = str(e)
            
        # Count runs
        try:
            count_runs = db.execute(text("SELECT COUNT(*) FROM crypto_forwards.run_main")).scalar()
            results["count_run_main"] = count_runs
            
            count_details = db.execute(text("SELECT COUNT(*) FROM crypto_forwards.run_details")).scalar()
            results["count_run_details"] = count_details
            
            # Get latest run
            latest_run = db.execute(text("SELECT * FROM crypto_forwards.run_main ORDER BY ran_at_utc DESC LIMIT 1")).mappings().all()
            if latest_run:
                results["latest_run"] = str(latest_run[0])
            else:
                results["latest_run"] = "None"
        except Exception as e:
            results["count_run_main_error"] = str(e)
            
    except Exception as e:
        results["global_error"] = str(e)
        
    # Inspector details
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.get_bind())
        results["tables_in_public"] = inspector.get_table_names(schema="public")
        results["tables_in_crypto"] = inspector.get_table_names(schema="crypto_forwards")
        
        if "assets" in results["tables_in_public"]:
            results["assets_columns"] = [c["name"] for c in inspector.get_columns("assets", schema="public")]
    except Exception as e:
        results["inspector_error"] = str(e)

    return results

@router.post("/trigger-fetch/{symbol}")
async def trigger_fetch(symbol: str):
    from src.scripts.fetch_market_data import process_asset
    try:
        process_asset(symbol)
        return {"status": "success", "message": f"Processed {symbol}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/logs/scheduler")
async def get_scheduler_logs():
    return read_logs("logs/scheduler.log")

@router.get("/logs/scheduler-stderr")
async def get_scheduler_stderr():
    return read_logs("logs/scheduler_stderr.log")

@router.get("/logs/fetch")
async def get_fetch_logs():
    return read_logs("logs/fetch_market.log")

@router.get("/logs/list")
async def list_logs():
    import os
    if not os.path.exists("logs"):
        return {"error": "logs directory does not exist"}
    return {"files": os.listdir("logs")}

def read_logs(filepath, max_lines=100):
    import os
    if not os.path.exists(filepath):
        return {"error": f"Log file not found at {filepath}"}
    
    try:
        with open(filepath, "r") as f:
            # Read last N lines
            lines = f.readlines()
            return {"lines": lines[-max_lines:], "total_lines": len(lines)}
    except Exception as e:
        return {"error": str(e)}

@router.get("/logs/scheduler-full")
async def get_scheduler_logs_full():
    """Get full scheduler logs (up to 500 lines) for debugging"""
    return read_logs("logs/scheduler.log", max_lines=500)

@router.get("/processes")
async def check_processes():
    import subprocess
    try:
        # ps aux is standard, but ps might not be installed.
        # Try a few commands
        # ps aux is standard, but ps might not be installed.
        # Try a few commands
        try:
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return {"processes": result.stdout.split("\n")}
        except FileNotFoundError:
            pass # Try next method
        
        # If ps failed, try 'top -b -n 1'
        result = subprocess.run(["top", "-b", "-n", "1"], capture_output=True, text=True)
        if result.returncode == 0:
           return {"top": result.stdout.split("\n")}
           
        return {"error": "Could not list processes (ps/top missing?)"}
    except Exception as e:
        return {"error": str(e)}


# =========== DATA LAYER EXTRACTION ENDPOINTS ===========

@router.get("/layers/bronze")
async def get_bronze_data(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get raw data from the Bronze layer (bronze.raw_vaults).
    Returns the unprocessed Hyperliquid vault data.
    """
    try:
        query = text("""
            SELECT id, vault_address, url, raw_content, response_metadata, 
                   ingested_at, processed_to_silver
            FROM bronze.raw_vaults
            ORDER BY ingested_at DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).mappings().all()
        
        # Convert to list of dicts
        data = []
        for row in result:
            row_dict = dict(row)
            # Convert datetime to string for JSON serialization
            if row_dict.get("ingested_at"):
                row_dict["ingested_at"] = str(row_dict["ingested_at"])
            data.append(row_dict)
            
        return {
            "layer": "bronze",
            "table": "bronze.raw_vaults",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "layer": "bronze"}


@router.get("/layers/silver/positions")
async def get_silver_positions(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get parsed position data from the Silver layer (bronze.hyperliquid_positions).
    Contains parsed and normalized position data.
    """
    try:
        query = text("""
            SELECT id, vault_address, user_address, coin, entry_price, mark_price,
                   position_size, position_value, margin_used, unrealized_pnl,
                   return_on_equity, liquidation_px, max_leverage, leverage_type,
                   leverage_value, cum_funding_all_time, cum_funding_since_open,
                   cum_funding_since_change, timestamp, source_origin
            FROM bronze.hyperliquid_positions
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).mappings().all()
        
        data = []
        for row in result:
            row_dict = dict(row)
            if row_dict.get("timestamp"):
                row_dict["timestamp"] = str(row_dict["timestamp"])
            # Convert Decimal types to float for JSON serialization
            for key, value in row_dict.items():
                if hasattr(value, '__float__'):
                    row_dict[key] = float(value) if value is not None else None
            data.append(row_dict)
            
        return {
            "layer": "silver",
            "table": "bronze.hyperliquid_positions",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "layer": "silver/positions"}


@router.get("/layers/silver/aggregated")
async def get_silver_aggregated(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get aggregated data from the Silver layer (silver.hyperliquid_aggregated).
    Contains calculated fields like direction and scaled values.
    """
    try:
        query = text("""
            SELECT id, source_position_id, vault_address, user_address, coin,
                   entry_price, mark_price, position_size, position_value,
                   margin_used, unrealized_pnl, direction,
                   pos_value_millions_long, pos_value_millions_short,
                   margin_thousands_long, margin_thousands_short,
                   timestamp, processed_at
            FROM silver.hyperliquid_aggregated
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).mappings().all()
        
        data = []
        for row in result:
            row_dict = dict(row)
            if row_dict.get("timestamp"):
                row_dict["timestamp"] = str(row_dict["timestamp"])
            if row_dict.get("processed_at"):
                row_dict["processed_at"] = str(row_dict["processed_at"])
            # Convert Decimal types to float for JSON serialization
            for key, value in row_dict.items():
                if hasattr(value, '__float__'):
                    row_dict[key] = float(value) if value is not None else None
            data.append(row_dict)
            
        return {
            "layer": "silver",
            "table": "silver.hyperliquid_aggregated",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "layer": "silver/aggregated"}


@router.get("/layers/gold")
async def get_gold_data(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get summarized data from the Gold layer (gold.hyperliquid_summary view).
    Contains aggregated financial metrics by timestamp.
    """
    try:
        query = text("""
            SELECT timestamp, total_position_value_millions,
                   longs_position_value_millions, shorts_position_value_millions,
                   longs_margin_thousands, shorts_margin_thousands,
                   net_margin_thousands, position_count
            FROM gold.hyperliquid_summary
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).mappings().all()
        
        data = []
        for row in result:
            row_dict = dict(row)
            if row_dict.get("timestamp"):
                row_dict["timestamp"] = str(row_dict["timestamp"])
            # Convert Decimal types to float for JSON serialization
            for key, value in row_dict.items():
                if hasattr(value, '__float__'):
                    row_dict[key] = float(value) if value is not None else None
            data.append(row_dict)
            
        return {
            "layer": "gold",
            "table": "gold.hyperliquid_summary",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "layer": "gold"}


@router.get("/layers/all")
async def get_all_layers(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get a sample of data from all layers (bronze, silver, gold).
    Useful for debugging the entire pipeline at once.
    """
    results = {
        "bronze": None,
        "silver_positions": None,
        "silver_aggregated": None,
        "gold": None
    }
    
    # Bronze
    try:
        bronze_result = await get_bronze_data(limit=limit, db=db)
        results["bronze"] = bronze_result
    except Exception as e:
        results["bronze"] = {"error": str(e)}
    
    # Silver positions
    try:
        silver_pos_result = await get_silver_positions(limit=limit, db=db)
        results["silver_positions"] = silver_pos_result
    except Exception as e:
        results["silver_positions"] = {"error": str(e)}
    
    # Silver aggregated
    try:
        silver_agg_result = await get_silver_aggregated(limit=limit, db=db)
        results["silver_aggregated"] = silver_agg_result
    except Exception as e:
        results["silver_aggregated"] = {"error": str(e)}
    
    # Gold
    try:
        gold_result = await get_gold_data(limit=limit, db=db)
        results["gold"] = gold_result
    except Exception as e:
        results["gold"] = {"error": str(e)}
    
    return results

