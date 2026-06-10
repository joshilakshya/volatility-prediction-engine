import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import settings
from api.routes import data, volatility, predict, events, vix

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("volatility_engine")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Volatility Prediction Engine — S&P 500 & Multi-Asset",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(volatility.router)
app.include_router(predict.router)
app.include_router(events.router)
app.include_router(vix.router)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", include_in_schema=False)
def serve_ui():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": f"{settings.app_name} v{settings.version} — visit /docs"}

@app.on_event("startup")
async def startup():
    logger.info(f"🚀  {settings.app_name} v{settings.version} — ready")
