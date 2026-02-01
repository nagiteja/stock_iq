import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router


def _configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = logging.getLevelName(level_name)
    logging.basicConfig(
        level=level if isinstance(level, int) else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


_configure_logging()

app = FastAPI(title="StockIQ")
app.include_router(api_router, prefix="/api")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_PATH = STATIC_DIR / "index.html"

if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/{path:path}")
async def serve_spa(path: str) -> FileResponse:
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if INDEX_PATH.exists():
        return FileResponse(INDEX_PATH)
    raise HTTPException(status_code=404, detail="Frontend not built")
