"""
CLI output parsing utilities for Google Group Maker.

This module contains functions to parse the output of the groupmaker.py CLI tool
and extract structured data from formatted text output. The CLI outputs data in
fixed-width column formats that need to be parsed into Python dictionaries.

Expected CLI Output Formats:
----------------------------

Groups List (parse_groups_output):
    EMAIL ADDRESS       NAME                            DESCRIPTION
    (40 chars)          (30 chars)                      (remaining)
    ----------------------------------------------------------------------------------
    group@domain.com    Group Display Name              Optional description text

Members List (parse_members_output):
    EMAIL ADDRESS                        NAME                     ROLE            TYPE      STATUS
    (45 chars)                           (25 chars)               (15 chars)      (10 chars)(remaining)
    --------------------------------------------------------------------------------------------------------
    member@domain.com                    Member Name              MEMBER          USER      ACTIVE
    owner@domain.com                     Owner Name               👑 OWNER        USER      ACTIVE

Note: Role markers (👑 for OWNER, ⭐ for MANAGER) are stripped during parsing.
"""

import re
from typing import List, Dict

# Compiled email validation pattern for performance (used by _validate_email)
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Public API
__all__ = [
    'parse_groups_output',
    'parse_members_output',
    'parse_email_list',
    'validate_email'
]


def _validate_email(email: str) -> bool:
    """Validate an email address format.

    Uses standard email regex pattern aligned with CLI tool expectations.

    Args:
        email: Email address string to validate

    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_email(email: str) -> bool:
    """Validate an email address format (public API).
    
    Args:
        email: Email address string to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    return _validate_email(email)


def parse_groups_output(output: str) -> List[Dict[str, str]]:
    """Parse the groups list CLI output into structured data.
    
    The CLI outputs groups in a fixed-width table format:
    EMAIL ADDRESS (40 chars) NAME (30 chars) DESCRIPTION
    
    Args:
        output: Raw CLI stdout containing groups list
        
    Returns:
        List of group dictionaries with keys: email, name, description
    """
    groups = []
    lines = output.strip().split('\n')
    
    # Look for the header line with dashes
    header_found = False
    for i, line in enumerate(lines):
        if line.startswith('-' * 20):  # Look for separator line
            header_found = True
            continue
        
        if header_found and line.strip() and not line.startswith('-'):
            # Parse the formatted output
            # Format: EMAIL ADDRESS (40 chars) NAME (30 chars) DESCRIPTION
            if len(line) >= 40:
                email = line[:40].strip()
                remaining = line[40:]
                if len(remaining) >= 30:
                    name = remaining[:30].strip()
                    description = remaining[30:].strip()
                else:
                    name = remaining.strip()
                    description = ""
                
                if email and email != 'EMAIL ADDRESS':  # Skip header row
                    groups.append({
                        "email": email,
                        "name": name,
                        "description": description
                    })
    
    return groups


def parse_members_output(output: str) -> List[Dict[str, str]]:
    """Parse the members list CLI output into structured data.
    
    The CLI outputs members in a fixed-width table format:
    EMAIL ADDRESS (45) NAME (25) ROLE (15) TYPE (10) STATUS
    
    Role markers (👑 for OWNER, ⭐ for MANAGER) are stripped from output.
    
    Args:
        output: Raw CLI stdout containing members list
        
    Returns:
        List of member dictionaries with keys: email, name, role, type, status
    """
    members = []
    lines = output.strip().split('\n')
    
    # Look for the header line with dashes
    header_found = False
    for i, line in enumerate(lines):
        if line.startswith('-' * 20):  # Look for separator line
            header_found = True
            continue
            
        if header_found and line.strip() and not line.startswith('-') and not line.startswith('Summary:'):
            # Parse the formatted output
            # Format: EMAIL ADDRESS (45) NAME (25) ROLE (15) TYPE (10) STATUS
            if len(line) >= 45:
                email = line[:45].strip()
                remaining = line[45:]
                
                if len(remaining) >= 25:
                    name = remaining[:25].strip()
                    remaining = remaining[25:]
                    
                    if len(remaining) >= 15:
                        role = remaining[:15].strip()
                        # Remove emoji markers
                        role = role.replace('👑 ', '').replace('⭐ ', '').strip()
                        remaining = remaining[15:]
                        
                        if len(remaining) >= 10:
                            member_type = remaining[:10].strip()
                            status = remaining[10:].strip()
                        else:
                            member_type = remaining.strip()
                            status = ""
                    else:
                        role = remaining.strip()
                        member_type = ""
                        status = ""
                else:
                    name = remaining.strip()
                    role = ""
                    member_type = ""
                    status = ""
                
                if email and email != 'EMAIL ADDRESS':  # Skip header row
                    members.append({
                        "email": email,
                        "name": name,
                        "role": role,
                        "type": member_type,
                        "status": status
                    })
    
    return members


def parse_email_list(text: str) -> List[str]:
    """Parse a text input containing multiple email addresses.

    Supports multiple delimiters: newlines, commas, semicolons, spaces.
    Automatically deduplicates and validates email addresses using the same
    validation logic as the CLI tool for consistency.

    Args:
        text: Text containing one or more email addresses

    Returns:
        List of valid, deduplicated email addresses
    """
    if not text:
        return []
    
    # Split by common delimiters
    emails = []
    for delimiter in ['\n', ',', ';', ' ']:
        if delimiter in text:
            parts = text.split(delimiter)
            for part in parts:
                part = part.strip()
                if part and '@' in part:
                    emails.append(part)
            break
    else:
        # No delimiter found, treat as single email
        if text.strip() and '@' in text.strip():
            emails.append(text.strip())
    
    # Deduplicate and validate
    valid_emails = []
    for email in emails:
        email = email.strip()
        if email and email not in valid_emails and _validate_email(email):
            valid_emails.append(email)
    
    return valid_emails