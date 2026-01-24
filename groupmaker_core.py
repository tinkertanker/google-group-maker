"""
Google Groups Core Library

Extracted business logic from groupmaker.py for use in both CLI and web applications.
This module provides importable functions that return structured data instead of printing.
"""

from __future__ import annotations

import os
import re
import json
import time
from dataclasses import dataclass
from typing import Optional

from googleapiclient.discovery import build, Resource
from google.oauth2 import service_account


# Default configuration from environment
DEFAULT_DOMAIN = os.environ.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com")
DEFAULT_EMAIL = os.environ.get("DEFAULT_EMAIL")
DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or DEFAULT_EMAIL

# API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.group',
    'https://www.googleapis.com/auth/admin.directory.group.member'
]


@dataclass
class OperationResult:
    """Result of an operation."""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation."""
    valid: bool
    group_name: Optional[str] = None
    domain: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CredentialsResult:
    """Result of loading credentials."""
    credentials: Optional[dict] = None
    source: str = "missing"  # 'env', 'file', 'invalid-env', 'invalid-file', 'missing'
    error: Optional[str] = None


def load_credentials(
    env_var: str = "GOOGLE_SERVICE_ACCOUNT_JSON",
    file_path: str = "service-account-credentials.json"
) -> CredentialsResult:
    """
    Load service account credentials from environment or file.

    Args:
        env_var: Environment variable name containing JSON credentials
        file_path: Path to credentials file

    Returns:
        CredentialsResult with credentials dict or error info
    """
    # First try environment variable
    env_json = os.environ.get(env_var)
    if env_json:
        try:
            creds_dict = json.loads(env_json)
            return CredentialsResult(credentials=creds_dict, source='env')
        except json.JSONDecodeError as e:
            return CredentialsResult(
                source='invalid-env',
                error=f"Invalid JSON in {env_var}: {e}"
            )

    # Fall back to file
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                creds_dict = json.load(f)
            return CredentialsResult(credentials=creds_dict, source='file')
        except json.JSONDecodeError as e:
            return CredentialsResult(
                source='invalid-file',
                error=f"Invalid JSON in {file_path}: {e}"
            )
        except Exception as e:
            return CredentialsResult(
                source='missing',
                error=f"Failed to read {file_path}: {e}"
            )

    return CredentialsResult(
        source='missing',
        error="No credentials found. Provide via environment variable or file."
    )


def create_service(
    credentials_dict: Optional[dict] = None,
    admin_email: Optional[str] = None
) -> Optional[Resource]:
    """
    Create and return an authorised Google Directory API service.

    Args:
        credentials_dict: Service account credentials. If None, loads from env/file.
        admin_email: Admin email for delegation. Defaults to DEFAULT_ADMIN_EMAIL.

    Returns:
        Google Directory API service or None if failed
    """
    if credentials_dict is None:
        result = load_credentials()
        if result.credentials is None:
            return None
        credentials_dict = result.credentials

    delegated_email = admin_email or DEFAULT_ADMIN_EMAIL
    if not delegated_email:
        return None

    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict, scopes=SCOPES
    )
    delegated_credentials = credentials.with_subject(delegated_email)

    return build('admin', 'directory_v1', credentials=delegated_credentials)


def validate_group_name(group_name: str) -> ValidationResult:
    """
    Validate a group name or email address.

    Accepts:
    - Simple group name: 'class-a-2023'
    - Full email: 'class-a-2023@example.com'

    Returns:
        ValidationResult with parsed name and domain
    """
    domain_from_email = None
    name = group_name

    if '@' in group_name:
        parts = group_name.split('@')
        if len(parts) != 2:
            return ValidationResult(
                valid=False,
                error=f"Invalid email format '{group_name}'. Use 'group-name@domain.com'."
            )
        name, domain_from_email = parts

    # Check valid characters
    if not re.match(r'^[a-zA-Z0-9.\-_]+$', name):
        return ValidationResult(
            valid=False,
            error=f"Group name '{name}' contains invalid characters. "
                  "Only letters, numbers, periods, hyphens, and underscores allowed."
        )

    return ValidationResult(valid=True, group_name=name, domain=domain_from_email)


def validate_email(email: str) -> bool:
    """Validate an email address format."""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def create_group(
    service: Resource,
    group_name: str,
    domain: Optional[str] = None,
    description: str = ""
) -> OperationResult:
    """
    Create a new Google Group.

    Args:
        service: Google Directory API service
        group_name: Name of the group (without domain)
        domain: Domain for the group email
        description: Optional group description

    Returns:
        OperationResult with created group data
    """
    domain_to_use = domain or DEFAULT_DOMAIN
    email = f"{group_name}@{domain_to_use}"

    group_body = {
        "email": email,
        "name": group_name,
        "description": description,
        "allowExternalMembers": True,
        "whoCanJoin": "INVITED_CAN_JOIN",
        "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
        "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
        "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",
        "allowWebPosting": True,
        "includeInGlobalAddressList": True
    }

    try:
        result = service.groups().insert(body=group_body).execute()
        return OperationResult(
            success=True,
            message=f"Group '{email}' created successfully",
            data=result
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message=f"Failed to create group '{email}'",
            error=str(e)
        )


def get_group(service: Resource, group_email: str) -> OperationResult:
    """
    Get a Google Group by email.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group

    Returns:
        OperationResult with group data
    """
    try:
        result = service.groups().get(groupKey=group_email).execute()
        return OperationResult(
            success=True,
            message=f"Group '{group_email}' found",
            data=result
        )
    except Exception as e:
        error_str = str(e)
        if "Resource Not Found" in error_str:
            return OperationResult(
                success=False,
                message=f"Group '{group_email}' not found",
                error="Group does not exist"
            )
        return OperationResult(
            success=False,
            message=f"Failed to get group '{group_email}'",
            error=error_str
        )


def ensure_group_exists(
    service: Resource,
    group_email: str,
    max_attempts: int = 3,
    delay: float = 3.0
) -> bool:
    """
    Check if a group exists and wait for propagation if needed.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group
        max_attempts: Maximum retries
        delay: Seconds between retries

    Returns:
        True if group exists, False otherwise
    """
    for attempt in range(max_attempts):
        result = get_group(service, group_email)
        if result.success:
            return True
        if attempt < max_attempts - 1:
            time.sleep(delay)
    return False


def delete_group(service: Resource, group_email: str) -> OperationResult:
    """
    Delete a Google Group.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group

    Returns:
        OperationResult indicating success/failure
    """
    # First check if group exists
    check = get_group(service, group_email)
    if not check.success:
        return check

    try:
        service.groups().delete(groupKey=group_email).execute()
        return OperationResult(
            success=True,
            message=f"Group '{group_email}' deleted successfully"
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message=f"Failed to delete group '{group_email}'",
            error=str(e)
        )


def rename_group(
    service: Resource,
    old_email: str,
    new_name: str,
    new_domain: Optional[str] = None
) -> OperationResult:
    """
    Rename a Google Group.

    Args:
        service: Google Directory API service
        old_email: Current full email address
        new_name: New name for the group
        new_domain: New domain (defaults to same as old)

    Returns:
        OperationResult with updated group data
    """
    # Get current group
    check = get_group(service, old_email)
    if not check.success:
        return check

    # Determine new email
    if new_domain:
        new_email = f"{new_name}@{new_domain}"
    else:
        # Extract domain from old email
        _, old_domain = old_email.split('@')
        new_email = f"{new_name}@{old_domain}"

    # Check if new email already exists
    new_check = get_group(service, new_email)
    if new_check.success:
        return OperationResult(
            success=False,
            message=f"Cannot rename: group '{new_email}' already exists",
            error="Target group already exists"
        )

    try:
        group = check.data
        group['email'] = new_email
        group['name'] = new_name

        result = service.groups().update(groupKey=old_email, body=group).execute()
        return OperationResult(
            success=True,
            message=f"Group renamed from '{old_email}' to '{new_email}'",
            data=result
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message=f"Failed to rename group",
            error=str(e)
        )


def list_groups(
    service: Resource,
    domain: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 100
) -> OperationResult:
    """
    List Google Groups in a domain.

    Args:
        service: Google Directory API service
        domain: Domain to list groups from
        query: Optional filter string
        max_results: Maximum results per page

    Returns:
        OperationResult with list of groups
    """
    domain_to_use = domain or DEFAULT_DOMAIN
    groups = []
    page_token = None

    try:
        while True:
            params = {
                'domain': domain_to_use,
                'maxResults': max_results
            }
            if page_token:
                params['pageToken'] = page_token

            results = service.groups().list(**params).execute()

            if 'groups' in results:
                if query:
                    # Filter locally
                    query_lower = query.lower()
                    filtered = [
                        g for g in results['groups']
                        if (query_lower in g.get('email', '').lower() or
                            query_lower in g.get('name', '').lower() or
                            query_lower in g.get('description', '').lower())
                    ]
                    groups.extend(filtered)
                else:
                    groups.extend(results['groups'])

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return OperationResult(
            success=True,
            message=f"Found {len(groups)} groups",
            data={'groups': groups, 'domain': domain_to_use}
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to list groups",
            error=str(e)
        )


def add_member(
    service: Resource,
    group_email: str,
    member_email: str,
    role: str = "MEMBER",
    retry: bool = True
) -> OperationResult:
    """
    Add a member to a Google Group.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group
        member_email: Email of member to add
        role: Role to assign (OWNER, MANAGER, MEMBER)
        retry: Whether to retry if group not found

    Returns:
        OperationResult indicating success/failure
    """
    member_body = {
        "email": member_email,
        "role": role,
        "delivery_settings": "ALL_MAIL"
    }

    try:
        result = service.members().insert(
            groupKey=group_email,
            body=member_body
        ).execute()
        return OperationResult(
            success=True,
            message=f"Added {member_email} to {group_email} as {role}",
            data=result
        )
    except Exception as e:
        error_str = str(e)
        if retry and "Resource Not Found: groupKey" in error_str:
            # Group may still be propagating
            time.sleep(5)
            return add_member(service, group_email, member_email, role, retry=False)

        if "Member already exists" in error_str:
            return OperationResult(
                success=False,
                message=f"{member_email} is already a member of {group_email}",
                error="Member already exists"
            )

        return OperationResult(
            success=False,
            message=f"Failed to add {member_email} to {group_email}",
            error=error_str
        )


def remove_member(
    service: Resource,
    group_email: str,
    member_email: str
) -> OperationResult:
    """
    Remove a member from a Google Group.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group
        member_email: Email of member to remove

    Returns:
        OperationResult indicating success/failure
    """
    try:
        service.members().delete(
            groupKey=group_email,
            memberKey=member_email
        ).execute()
        return OperationResult(
            success=True,
            message=f"Removed {member_email} from {group_email}"
        )
    except Exception as e:
        error_str = str(e)
        if "Resource Not Found" in error_str:
            if "memberKey" in error_str:
                return OperationResult(
                    success=False,
                    message=f"{member_email} is not a member of {group_email}",
                    error="Member not found"
                )
            return OperationResult(
                success=False,
                message=f"Group {group_email} not found",
                error="Group not found"
            )
        return OperationResult(
            success=False,
            message=f"Failed to remove {member_email} from {group_email}",
            error=error_str
        )


def list_members(
    service: Resource,
    group_email: str,
    include_derived: bool = False,
    max_results: int = 100
) -> OperationResult:
    """
    List members of a Google Group.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group
        include_derived: Include members from nested groups
        max_results: Maximum results per page

    Returns:
        OperationResult with list of members
    """
    members = []
    page_token = None

    try:
        while True:
            params = {
                'groupKey': group_email,
                'maxResults': max_results,
                'includeDerivedMembership': include_derived
            }
            if page_token:
                params['pageToken'] = page_token

            results = service.members().list(**params).execute()

            if 'members' in results:
                members.extend(results['members'])

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        # Sort by role
        role_order = {'OWNER': 0, 'MANAGER': 1, 'MEMBER': 2}
        members.sort(key=lambda m: (
            role_order.get(m.get('role', 'MEMBER'), 3),
            m.get('email', '')
        ))

        # Count by role
        owners = sum(1 for m in members if m.get('role') == 'OWNER')
        managers = sum(1 for m in members if m.get('role') == 'MANAGER')
        regular = sum(1 for m in members if m.get('role') == 'MEMBER')

        return OperationResult(
            success=True,
            message=f"Found {len(members)} members in {group_email}",
            data={
                'members': members,
                'group_email': group_email,
                'summary': {
                    'total': len(members),
                    'owners': owners,
                    'managers': managers,
                    'members': regular
                }
            }
        )
    except Exception as e:
        error_str = str(e)
        if "Resource Not Found" in error_str:
            return OperationResult(
                success=False,
                message=f"Group {group_email} not found",
                error="Group not found"
            )
        return OperationResult(
            success=False,
            message=f"Failed to list members of {group_email}",
            error=error_str
        )


def update_member_role(
    service: Resource,
    group_email: str,
    member_email: str,
    new_role: str
) -> OperationResult:
    """
    Update a member's role in a Google Group.

    Args:
        service: Google Directory API service
        group_email: Full email address of the group
        member_email: Email of member to update
        new_role: New role (OWNER, MANAGER, MEMBER)

    Returns:
        OperationResult indicating success/failure
    """
    if new_role not in ('OWNER', 'MANAGER', 'MEMBER'):
        return OperationResult(
            success=False,
            message=f"Invalid role: {new_role}",
            error="Role must be OWNER, MANAGER, or MEMBER"
        )

    try:
        result = service.members().update(
            groupKey=group_email,
            memberKey=member_email,
            body={"role": new_role}
        ).execute()
        return OperationResult(
            success=True,
            message=f"Updated {member_email} role to {new_role} in {group_email}",
            data=result
        )
    except Exception as e:
        error_str = str(e)
        if "Resource Not Found" in error_str:
            if "memberKey" in error_str:
                return OperationResult(
                    success=False,
                    message=f"{member_email} is not a member of {group_email}",
                    error="Member not found"
                )
            return OperationResult(
                success=False,
                message=f"Group {group_email} not found",
                error="Group not found"
            )
        return OperationResult(
            success=False,
            message=f"Failed to update {member_email} role",
            error=error_str
        )


def build_group_email(group_name: str, domain: Optional[str] = None) -> str:
    """
    Build a full group email from name and optional domain.

    Args:
        group_name: Group name (may include domain)
        domain: Optional domain override

    Returns:
        Full email address
    """
    if '@' in group_name:
        return group_name
    return f"{group_name}@{domain or DEFAULT_DOMAIN}"
