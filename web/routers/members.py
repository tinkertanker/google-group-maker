"""
Member management routes.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import groupmaker_core as core
from web.dependencies import (
    templates,
    require_auth,
    get_google_service,
    flash,
    get_flash_messages,
)

router = APIRouter()


@router.post("/groups/{group_email}/members")
async def add_member(
    request: Request,
    group_email: str,
    member_email: str = Form(...),
    role: str = Form("MEMBER"),
    user: dict = Depends(require_auth),
):
    """Add a member to a group."""
    if not core.validate_email(member_email):
        flash(request, f"Invalid email address: {member_email}", "error")
        return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)

    if role not in ("OWNER", "MANAGER", "MEMBER"):
        role = "MEMBER"

    service = get_google_service(request)
    result = core.add_member(service, group_email, member_email, role=role)

    if result.success:
        flash(request, f"Added {member_email} as {role}", "success")
    else:
        flash(request, f"Failed to add member: {result.error}", "error")

    return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)


@router.delete("/groups/{group_email}/members/{member_email}")
async def remove_member(
    request: Request,
    group_email: str,
    member_email: str,
    user: dict = Depends(require_auth),
):
    """Remove a member from a group (htmx endpoint)."""
    service = get_google_service(request)
    result = core.remove_member(service, group_email, member_email)

    if result.success:
        # Return empty response for htmx to remove the row
        return HTMLResponse(content="", status_code=200)
    else:
        return HTMLResponse(
            content=f'<div class="text-red-600 text-sm">Failed: {result.error}</div>',
            status_code=400,
        )


@router.post("/groups/{group_email}/members/{member_email}/remove")
async def remove_member_form(
    request: Request,
    group_email: str,
    member_email: str,
    user: dict = Depends(require_auth),
):
    """Remove a member from a group (form submission fallback)."""
    service = get_google_service(request)
    result = core.remove_member(service, group_email, member_email)

    if result.success:
        flash(request, f"Removed {member_email}", "success")
    else:
        flash(request, f"Failed to remove: {result.error}", "error")

    return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)


@router.post("/groups/{group_email}/members/{member_email}/role")
async def update_member_role(
    request: Request,
    group_email: str,
    member_email: str,
    role: str = Form(...),
    user: dict = Depends(require_auth),
):
    """Update a member's role."""
    if role not in ("OWNER", "MANAGER", "MEMBER"):
        flash(request, "Invalid role", "error")
        return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)

    service = get_google_service(request)
    result = core.update_member_role(service, group_email, member_email, role)

    if result.success:
        flash(request, f"Updated {member_email} to {role}", "success")
    else:
        flash(request, f"Failed to update role: {result.error}", "error")

    return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)


@router.patch("/groups/{group_email}/members/{member_email}")
async def update_member_role_htmx(
    request: Request,
    group_email: str,
    member_email: str,
    user: dict = Depends(require_auth),
):
    """Update a member's role (htmx endpoint)."""
    form = await request.form()
    role = form.get("role", "MEMBER")

    if role not in ("OWNER", "MANAGER", "MEMBER"):
        return HTMLResponse(
            content='<div class="text-red-600 text-sm">Invalid role</div>',
            status_code=400,
        )

    service = get_google_service(request)
    result = core.update_member_role(service, group_email, member_email, role)

    if result.success:
        return HTMLResponse(
            content=f'<span class="text-green-600">{role}</span>',
            status_code=200,
        )
    else:
        return HTMLResponse(
            content=f'<div class="text-red-600 text-sm">Failed: {result.error}</div>',
            status_code=400,
        )
