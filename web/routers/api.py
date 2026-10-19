"""
Token-authenticated JSON API exposing safe operations only.

Intended for automation (Slack workflows, scripts, shortcuts) that cannot
use the browser OAuth flow. Deliberately limited surface:

    GET  /api/groups
    GET  /api/groups/{group_email}/members
    POST /api/groups
    POST /api/groups/{group_email}/members

Destructive or disruptive actions (delete, rename, remove member, role
changes) are not available here — use the web UI.

Auth: X-API-Key header — accepts minted keys (stored hashed in SQLite,
managed at /keys) or the API_KEY env var as a master/bootstrap key.
Every call is recorded in the api_audit table.

Endpoints are plain `def` so blocking Google calls run in the threadpool.
"""

import hmac
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import groupmaker_core as core
from web import alerts, apikeys
from web.dependencies import AVAILABLE_DOMAINS, DEFAULT_DOMAIN, get_google_service

router = APIRouter()

API_KEY = os.environ.get("API_KEY", "")

# Registers the apiKey scheme in OpenAPI so /docs gets an Authorize button.
api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(provided: Optional[str] = Depends(api_key_scheme)) -> dict:
    """Require a valid X-API-Key header. Returns the matched key's info."""
    if not provided:
        alerts.notify_auth_failure("missing X-API-Key header")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    # Master key from env (bootstrap / recovery if the key DB is lost)
    if API_KEY and hmac.compare_digest(provided.encode(), API_KEY.encode()):
        return {"id": None, "name": "env API_KEY", "prefix": "env"}
    key = apikeys.lookup_key(provided)
    if not key:
        alerts.notify_auth_failure(f"invalid or revoked key ({provided[:12]}…)")
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return key


def _record(key: dict, action: str, detail: str, status: int) -> None:
    """Write the audit row and fire the Slack alert for one API call."""
    apikeys.log_action(key, action, detail, status)
    alerts.notify_api_use(key, action, detail, status)


def _fail(key: dict, action: str, detail: str, status: int, message: str) -> None:
    """Audit and alert a rejected authenticated call, then raise."""
    _record(key, action, detail, status)
    raise HTTPException(status_code=status, detail=message)


def check_group_email(group_email: str, key: dict, action: str) -> None:
    """Ensure the target is a well-formed email in a domain we manage."""
    if not core.validate_email(group_email):
        _fail(key, action, group_email, 400, f"Invalid group email: {group_email}")
    domain = group_email.split("@")[-1]
    if domain not in AVAILABLE_DOMAINS:
        _fail(
            key,
            action,
            group_email,
            400,
            f"Group domain must be one of: {', '.join(AVAILABLE_DOMAINS)}",
        )


def add_member_result(service, group_email: str, email: str) -> dict:
    """Add one member as MEMBER, returning a per-member result dict."""
    if not core.validate_email(email):
        return {"email": email, "success": False, "error": "Invalid email address"}
    result = core.add_member(service, group_email, email, role="MEMBER")
    return {"email": email, "success": result.success, "error": result.error}


class CreateGroupRequest(BaseModel):
    name: str = Field(..., description="Group name, e.g. 'class-a-2024'")
    domain: Optional[str] = Field(
        None, description=f"One of: {', '.join(AVAILABLE_DOMAINS)}"
    )
    description: str = ""
    members: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Emails to add as MEMBER (max 50)",
    )


class AddMemberRequest(BaseModel):
    email: str


@router.get("/groups")
def list_groups(
    domain: Optional[str] = None,
    query: Optional[str] = None,
    key: dict = Depends(require_api_key),
    service=Depends(get_google_service),
):
    """List groups across allowed domains, optionally filtered."""
    if domain and domain not in AVAILABLE_DOMAINS:
        _fail(
            key,
            "list_groups",
            f"domain={domain}",
            400,
            f"Domain must be one of: {', '.join(AVAILABLE_DOMAINS)}",
        )
    domains = [domain] if domain else AVAILABLE_DOMAINS

    groups = []
    errors = {}
    for d in domains:
        result = core.list_groups(service, domain=d, query=query)
        if result.success:
            groups.extend(result.data.get("groups", []))
        else:
            errors[d] = result.error

    groups.sort(key=lambda g: g.get("email", "").lower())
    _record(
        key, "list_groups", f"domain={domain or 'all'} query={query or ''}", 200
    )
    return {"groups": groups, "count": len(groups), "errors": errors or None}


@router.get("/groups/{group_email}/members")
def list_members(
    group_email: str,
    key: dict = Depends(require_api_key),
    service=Depends(get_google_service),
):
    """List members of a group."""
    check_group_email(group_email, key, "list_members")
    result = core.list_members(service, group_email)
    if not result.success:
        status = 404 if "not found" in (result.error or "").lower() else 502
        _fail(key, "list_members", group_email, status, result.error)
    _record(key, "list_members", group_email, 200)
    return result.data


@router.post("/groups", status_code=201)
def create_group(
    body: CreateGroupRequest,
    key: dict = Depends(require_api_key),
    service=Depends(get_google_service),
):
    """Create a group and optionally add members (always as MEMBER)."""
    validation = core.validate_group_name(body.name)
    if not validation.valid:
        _fail(key, "create_group", body.name, 400, validation.error)

    domain = validation.domain or body.domain or DEFAULT_DOMAIN
    if domain not in AVAILABLE_DOMAINS:
        _fail(
            key,
            "create_group",
            body.name,
            400,
            f"Domain must be one of: {', '.join(AVAILABLE_DOMAINS)}",
        )

    result = core.create_group(
        service, validation.group_name, domain=domain, description=body.description
    )
    if not result.success:
        status = 409 if "already exists" in (result.error or "").lower() else 502
        _fail(key, "create_group", body.name, status, result.error)

    group_email = f"{validation.group_name}@{domain}"
    core.ensure_group_exists(service, group_email)

    member_results = [
        add_member_result(service, group_email, email) for email in body.members
    ]
    added = sum(1 for m in member_results if m["success"])
    _record(
        key, "create_group", f"{group_email} (+{added} members)", 201
    )

    return {"email": group_email, "group": result.data, "members": member_results}


@router.post("/groups/{group_email}/members", status_code=201)
def add_member(
    group_email: str,
    body: AddMemberRequest,
    key: dict = Depends(require_api_key),
    service=Depends(get_google_service),
):
    """Add a member to a group. Role is always MEMBER via the API."""
    check_group_email(group_email, key, "add_member")
    target = f"{body.email} -> {group_email}"

    if not core.validate_email(body.email):
        _fail(key, "add_member", target, 400, f"Invalid email: {body.email}")

    check = core.get_group(service, group_email)
    if not check.success:
        _fail(key, "add_member", target, 404, f"Group not found: {group_email}")

    result = core.add_member(service, group_email, body.email, role="MEMBER")
    if not result.success:
        status = 409 if "already exists" in (result.error or "").lower() else 502
        _fail(key, "add_member", target, status, result.error)

    _record(key, "add_member", target, 201)
    return {"group": group_email, "added": body.email, "role": "MEMBER"}
