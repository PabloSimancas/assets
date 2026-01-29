from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.infrastructure.database.session import get_db

router = APIRouter(
    prefix="/debug",
    tags=["debug"]
)

@router.get("/db")
async def debug_db(db: Session = Depends(get_db)):
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
        except Exception as e:
            results["count_run_main"] = str(e)
            
    except Exception as e:
        results["global_error"] = str(e)
        
    return results
