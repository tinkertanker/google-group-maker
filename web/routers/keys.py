"""
API key management UI.

Any logged-in user can mint and revoke keys — everyone here is an admin.
Minted keys are shown exactly once; only their hashes are stored.
The page also shows the audit log of what each key did.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web import apikeys
from web.dependencies import (
    flash,
    get_flash_messages,
    require_auth,
    templates,
)

router = APIRouter()


def render_keys_page(request: Request, user: dict, new_key: str = None):
    """Render the keys page, optionally showing a freshly minted key once."""
    return templates.TemplateResponse(
        "keys.html",
        {
            "request": request,
            "user": user,
            "keys": apikeys.list_keys(),
            "audit": apikeys.list_audit(100),
            "new_key": new_key,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.get("", response_class=HTMLResponse)
async def keys_page(request: Request, user: dict = Depends(require_auth)):
    """List keys and recent audit entries."""
    return render_keys_page(request, user)


@router.post("", response_class=HTMLResponse)
async def mint_key(
    request: Request,
    name: str = Form(...),
    user: dict = Depends(require_auth),
):
    """Mint a new key. Rendered once in the response — copy it now."""
    name = name.strip()[:64]
    if not name:
        flash(request, "Give the key a name (e.g. slack-workflow)", "error")
        return RedirectResponse(url="/keys", status_code=303)

    raw = apikeys.mint_key(name, user["email"])
    # Rendered directly (no redirect) so the key never enters the session
    # cookie — it's shown once and never stored anywhere.
    return render_keys_page(request, user, new_key=raw)


@router.post("/{key_id}/revoke")
async def revoke_key(
    request: Request,
    key_id: int,
    user: dict = Depends(require_auth),
):
    """Revoke a key."""
    if apikeys.revoke_key(key_id):
        flash(request, "Key revoked", "success")
    else:
        flash(request, "Key not found or already revoked", "warning")
    return RedirectResponse(url="/keys", status_code=303)
