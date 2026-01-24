"""
Authentication routes using Google OAuth.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth, OAuthError

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

# OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
ALLOWED_DOMAIN = os.environ.get("ALLOWED_DOMAIN", "")

# Set up OAuth
oauth = OAuth()

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Show login page or initiate OAuth.
    """
    # If user is already logged in, redirect to home
    if request.session.get("user"):
        return RedirectResponse(url="/")

    # If OAuth not configured, show login page with error
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            }
        )

    # Show login page
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/start")
async def start_oauth(request: Request):
    """
    Start the OAuth flow (called when user clicks login button).
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="OAuth not configured"
        )

    # Build redirect URI, respecting X-Forwarded-Proto from reverse proxy
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    redirect_uri = f"{proto}://{host}/auth/callback"

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request):
    """
    Handle OAuth callback from Google.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth not configured")

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.description}")

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    # Verify domain if configured
    email = user_info.get("email", "")
    if ALLOWED_DOMAIN:
        user_domain = email.split("@")[-1] if "@" in email else ""
        if user_domain != ALLOWED_DOMAIN:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Only users from {ALLOWED_DOMAIN} are allowed."
            )

    # Store user in session
    request.session["user"] = {
        "email": email,
        "name": user_info.get("name", ""),
        "picture": user_info.get("picture", ""),
    }

    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    """
    Log out the current user.
    """
    request.session.clear()
    return RedirectResponse(url="/auth/login")


@router.get("/me")
async def get_current_user_info(request: Request):
    """
    Get current user information (API endpoint).
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
