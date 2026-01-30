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

@router.get("/logs/fetch")
async def get_fetch_logs():
    return read_logs("logs/fetch_market.log")

def read_logs(filepath):
    import os
    if not os.path.exists(filepath):
        return {"error": f"Log file not found at {filepath}"}
    
    try:
        with open(filepath, "r") as f:
            # Read last 100 lines
            lines = f.readlines()
            return {"lines": lines[-100:]}
    except Exception as e:
        return {"error": str(e)}
