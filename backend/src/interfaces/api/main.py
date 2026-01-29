from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from src.interfaces.api.routers import health, assets, analysis, debug

app = FastAPI(title="Assets Dashboard API")

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
