"""
Google Group Maker - FastAPI Web Application

A modern web interface for managing Google Groups with OAuth authentication.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.routers import auth, groups, members
from web.dependencies import get_current_user, templates

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Google Group Maker web app...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Google Group Maker",
    description="Web interface for managing Google Groups",
    version="1.0.0",
    lifespan=lifespan,
)

# Session middleware for OAuth
SESSION_SECRET = os.environ.get("SESSION_SECRET", "change-me-in-production")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])
app.include_router(members.router, tags=["members"])


@app.get("/")
async def index(request: Request, user: dict = Depends(get_current_user)):
    """Redirect to groups list."""
    if not user:
        return RedirectResponse(url="/auth/login")
    return RedirectResponse(url="/groups")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
