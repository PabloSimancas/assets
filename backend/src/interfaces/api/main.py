from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from src.interfaces.api.routers import health, assets, analysis, debug
from src.infrastructure.database.session import engine, Base
from src.infrastructure.database.models import AssetModel

app = FastAPI(title="Assets Dashboard API")

# Ensure tables exist on startup
@app.on_event("startup")
def on_startup():
    # Debug DB Connection
    url_str = str(engine.url)
    if ":" in url_str and "@" in url_str:
        pass
    print(f"API Startup - Connecting to Database: {url_str.split('@')[-1] if '@' in url_str else url_str}")
    
    try:
        # Create Tables
        Base.metadata.create_all(bind=engine)
        
        # Verify Tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"API Startup - Found tables: {tables}")
        
        if "assets" not in tables:
             print("CRITICAL: 'assets' table missing after create_all!")
        
    except Exception as e:
        print(f"API Startup - DB Error: {e}")

# Trust Proxy Headers (Critical for EasyPanel/SSL Termination)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(debug.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Service is running"}
