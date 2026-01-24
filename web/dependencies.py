"""
Shared dependencies for FastAPI routes.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.templating import Jinja2Templates

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import groupmaker_core as core

# Templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Configuration
ALLOWED_DOMAIN = os.environ.get("ALLOWED_DOMAIN", "")
DEFAULT_DOMAIN = os.environ.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com")


def get_current_user(request: Request) -> Optional[dict]:
    """
    Get the current authenticated user from session.
    Returns None if not authenticated.
    """
    return request.session.get("user")


def require_auth(request: Request) -> dict:
    """
    Require authentication. Raises HTTPException if not authenticated.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_google_service(request: Request):
    """
    Get an authenticated Google Directory API service.
    Uses credentials from environment/file.

    Note: API calls are delegated to ADMIN_EMAIL/DEFAULT_EMAIL, not the
    logged-in user. The logged-in user is for web app auth only; the service
    account delegation requires a Google Workspace admin.
    """
    creds_result = core.load_credentials()
    if creds_result.credentials is None:
        raise HTTPException(
            status_code=500,
            detail=f"Service account credentials not configured: {creds_result.error}"
        )

    # Use configured admin email for delegation (not logged-in user)
    service = core.create_service(creds_result.credentials)
    if not service:
        raise HTTPException(
            status_code=500,
            detail="Failed to create Google Directory API service"
        )

    return service


def flash(request: Request, message: str, category: str = "info"):
    """
    Add a flash message to the session.
    Categories: info, success, warning, error
    """
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    request.session["flash_messages"].append({
        "message": message,
        "category": category
    })


def get_flash_messages(request: Request) -> list:
    """Get and clear flash messages from session."""
    messages = request.session.pop("flash_messages", [])
    return messages


def build_group_email(group_name: str, domain: Optional[str] = None) -> str:
    """Build full group email from name and optional domain."""
    if "@" in group_name:
        return group_name
    return f"{group_name}@{domain or DEFAULT_DOMAIN}"
