"""
Group management routes.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import groupmaker_core as core
from web.dependencies import (
    templates,
    require_auth,
    get_google_service,
    flash,
    get_flash_messages,
    build_group_email,
    DEFAULT_DOMAIN,
)

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def list_groups(
    request: Request,
    query: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """List all groups with optional search filter."""
    service = get_google_service(request)
    result = core.list_groups(service, domain=DEFAULT_DOMAIN, query=query)

    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "user": user,
            "groups": result.data.get("groups", []) if result.success else [],
            "query": query,
            "error": result.error if not result.success else None,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_group_form(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Show create group form."""
    return templates.TemplateResponse(
        "groups/new.html",
        {
            "request": request,
            "user": user,
            "default_domain": DEFAULT_DOMAIN,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.post("")
async def create_group(
    request: Request,
    group_name: str = Form(...),
    description: str = Form(""),
    trainer_emails: str = Form(""),
    add_self: bool = Form(False),
    user: dict = Depends(require_auth),
):
    """Create a new group."""
    # Validate group name
    validation = core.validate_group_name(group_name)
    if not validation.valid:
        flash(request, validation.error, "error")
        return RedirectResponse(url="/groups/new", status_code=303)

    service = get_google_service(request)
    domain = validation.domain or DEFAULT_DOMAIN

    # Create the group
    result = core.create_group(
        service,
        validation.group_name,
        domain=domain,
        description=description,
    )

    if not result.success:
        flash(request, f"Failed to create group: {result.error}", "error")
        return RedirectResponse(url="/groups/new", status_code=303)

    group_email = f"{validation.group_name}@{domain}"
    flash(request, f"Group {group_email} created successfully", "success")

    # Wait for group to propagate
    import time
    time.sleep(2)

    # Add trainer emails if provided
    errors = []
    if trainer_emails.strip():
        emails = [e.strip() for e in trainer_emails.replace(",", "\n").split("\n") if e.strip()]
        for email in emails:
            if core.validate_email(email):
                add_result = core.add_member(service, group_email, email)
                if not add_result.success:
                    errors.append(f"Failed to add {email}: {add_result.error}")
            else:
                errors.append(f"Invalid email: {email}")

    # Add self if requested
    if add_self:
        add_result = core.add_member(service, group_email, user["email"])
        if not add_result.success and "already exists" not in str(add_result.error):
            errors.append(f"Failed to add yourself: {add_result.error}")

    if errors:
        for err in errors:
            flash(request, err, "warning")

    return RedirectResponse(url=f"/groups/{group_email}/members", status_code=303)


@router.get("/{group_email}/members", response_class=HTMLResponse)
async def group_members(
    request: Request,
    group_email: str,
    rename: bool = False,
    user: dict = Depends(require_auth),
):
    """Show group members."""
    service = get_google_service(request)

    # Get group info
    group_result = core.get_group(service, group_email)
    if not group_result.success:
        flash(request, f"Group not found: {group_result.error}", "error")
        return RedirectResponse(url="/groups", status_code=303)

    # Get members
    members_result = core.list_members(service, group_email)

    return templates.TemplateResponse(
        "groups/members.html",
        {
            "request": request,
            "user": user,
            "group": group_result.data,
            "members": members_result.data.get("members", []) if members_result.success else [],
            "summary": members_result.data.get("summary", {}) if members_result.success else {},
            "error": members_result.error if not members_result.success else None,
            "rename_mode": rename,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.get("/{group_email}/edit")
async def edit_group_form(
    request: Request,
    group_email: str,
    user: dict = Depends(require_auth),
):
    """Redirect legacy edit page to the inline rename view."""
    return RedirectResponse(url=f"/groups/{group_email}/members?rename=1", status_code=303)


@router.post("/{group_email}/rename")
async def rename_group(
    request: Request,
    group_email: str,
    new_name: str = Form(...),
    user: dict = Depends(require_auth),
):
    """Rename a group."""
    new_name = new_name.strip()

    if "@" in new_name:
        flash(request, "Please enter only the group name before @, not the full email address.", "error")
        return RedirectResponse(url=f"/groups/{group_email}/members?rename=1", status_code=303)

    validation = core.validate_group_name(new_name)
    if not validation.valid:
        flash(request, validation.error, "error")
        return RedirectResponse(url=f"/groups/{group_email}/members?rename=1", status_code=303)

    service = get_google_service(request)

    # Extract domain from old email
    _, old_domain = group_email.split("@")
    new_domain = validation.domain or old_domain

    result = core.rename_group(service, group_email, validation.group_name, new_domain=new_domain)

    if result.success:
        new_email = f"{validation.group_name}@{new_domain}"
        flash(request, f"Group renamed to {new_email}", "success")
        return RedirectResponse(url=f"/groups/{new_email}/members", status_code=303)
    else:
        flash(request, f"Failed to rename: {result.error}", "error")
        return RedirectResponse(url=f"/groups/{group_email}/members?rename=1", status_code=303)


@router.delete("/{group_email}")
async def delete_group(
    request: Request,
    group_email: str,
    user: dict = Depends(require_auth),
):
    """Delete a group (htmx endpoint)."""
    service = get_google_service(request)
    result = core.delete_group(service, group_email)

    if result.success:
        flash(request, f"Group {group_email} deleted", "success")
        # Return htmx response to redirect
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = "/groups"
        return response
    else:
        return HTMLResponse(
            content=f'<div class="text-red-600">Failed: {result.error}</div>',
            status_code=400,
        )


@router.post("/{group_email}/delete")
async def delete_group_form(
    request: Request,
    group_email: str,
    user: dict = Depends(require_auth),
):
    """Delete a group (form submission)."""
    service = get_google_service(request)
    result = core.delete_group(service, group_email)

    if result.success:
        flash(request, f"Group {group_email} deleted", "success")
    else:
        flash(request, f"Failed to delete: {result.error}", "error")

    return RedirectResponse(url="/groups", status_code=303)
