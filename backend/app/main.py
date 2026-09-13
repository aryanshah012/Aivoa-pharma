"""FastAPI application entrypoint.

Run locally:   uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import complaints, dashboard, health
from app.core.config import get_settings
from app.db.init_db import init_db

settings = get_settings()

app = FastAPI(
    title="AIVOA PharmaQMS AI",
    description="AI-powered customer complaint management for pharmaceutical manufacturing. "
                "AI provides decision support; authorized Quality personnel make all final decisions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak stack traces or internals to the client."""
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})


app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(complaints.router)


from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.exists():
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = STATIC_DIR / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse(status_code=404, content={"detail": "Not found"})
else:
    @app.get("/")
    def root():
        return {"service": "AIVOA PharmaQMS AI", "docs": "/docs"}
