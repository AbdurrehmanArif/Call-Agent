"""
FastAPI application for the Call Agent.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path

from backend.routes.call_routes import router as call_router
from backend.utils.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"[STARTUP] Call Agent starting on {config.HOST}:{config.PORT}")
    print(f"[INFO] Debug mode: {config.DEBUG}")
    yield
    # Shutdown
    print("[SHUTDOWN] Call Agent shutting down...")


app = FastAPI(
    title="Call Agent API",
    description="AI-powered voice call handling system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    return frontend_dir / "index.html"


@app.get("/api")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "message": "Call Agent API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include routers
app.include_router(call_router, prefix="/api/calls", tags=["calls"])


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
