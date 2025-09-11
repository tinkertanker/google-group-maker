"""
Web utilities for Google Group Maker Streamlit app.

Provides a clean Python API for web UI operations.
"""

import re
import subprocess
import sys
import time
from typing import List, Dict, Optional, Any
import json
from pathlib import Path

class GroupMakerAPI:
    """API wrapper for Google Group Maker functionality."""
    
    def __init__(self, debug=False):
        self.debug = debug
    
    def _run_cli(self, args: List[str]) -> tuple[bool, str, str]:
        """Run the CLI command and return success status, stdout, stderr."""
        cmd = [sys.executable, "./groupmaker.py"] + args
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return proc.returncode == 0, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 60 seconds"
        except Exception as e:
            return False, "", str(e)
    
    def ping_auth(self) -> bool:
        """Test authentication by attempting to list groups."""
        try:
            success, stdout, stderr = self._run_cli(["list", "--max-results", "1"])
            if not success:
                raise RuntimeError(stderr or stdout or "Authentication failed")
            return True
        except Exception:
            raise
    
    def create_group(self, group_name: str, trainer_email: str, domain: Optional[str] = None, 
                     description: str = "", skip_self: bool = False) -> Dict[str, Any]:
        """Create a new Google Group."""
        args = ["create", group_name, trainer_email]
        
        if domain:
            args = ["--domain", domain] + args
        
        if description:
            args.append("--description")
            args.append(description)
            
        if skip_self:
            args.append("--skip-self")
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to create group")
        
        return {
            "success": True,
            "message": stdout.strip(),
            "group_name": group_name,
            "trainer_email": trainer_email
        }
    
    def list_groups(self, query: Optional[str] = None, domain: Optional[str] = None, 
                    max_results: int = 100) -> List[Dict[str, str]]:
        """List Google Groups, returning structured data."""
        args = ["list", "--max-results", str(max_results)]
        
        if domain:
            args = ["--domain", domain] + args
            
        if query:
            args.extend(["--query", query])
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to list groups")
        
        return self._parse_groups_output(stdout)
    
    def list_members(self, group_name: str, include_derived: bool = False, 
                     max_results: int = 100) -> List[Dict[str, str]]:
        """List members of a Google Group."""
        args = ["members", group_name, "--max-results", str(max_results)]
        
        if include_derived:
            args.append("--include-derived")
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to list members")
        
        return self._parse_members_output(stdout)
    
    def add_member(self, group_name: str, member_email: str, role: str = "MEMBER") -> Dict[str, Any]:
        """Add a single member to a Google Group."""
        args = ["add", group_name, member_email, "--role", role]
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to add member")
        
        return {
            "success": True,
            "message": stdout.strip(),
            "member_email": member_email,
            "role": role
        }
    
    def rename_group(self, old_group_name: str, new_group_name: str) -> Dict[str, Any]:
        """Rename an existing Google Group."""
        args = ["rename", old_group_name, new_group_name]
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to rename group")
        
        return {
            "success": True,
            "message": stdout.strip(),
            "old_name": old_group_name,
            "new_name": new_group_name
        }
    
    def delete_group(self, group_name: str) -> Dict[str, Any]:
        """Delete a Google Group (bypassing interactive confirmation)."""
        # We'll need to handle the confirmation programmatically
        # For now, we'll use a subprocess with input piping
        cmd = [sys.executable, "./groupmaker.py", "delete", group_name]
        
        try:
            proc = subprocess.run(cmd, input="yes\n", text=True, capture_output=True, timeout=60)
            success = proc.returncode == 0
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            raise RuntimeError("Command timed out after 60 seconds")
        except Exception as e:
            raise RuntimeError(str(e))
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to delete group")
        
        return {
            "success": True,
            "message": stdout.strip(),
            "group_name": group_name
        }
    
    def _parse_groups_output(self, output: str) -> List[Dict[str, str]]:
        """Parse the groups list output into structured data."""
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
    
    def _parse_members_output(self, output: str) -> List[Dict[str, str]]:
        """Parse the members list output into structured data."""
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
    
    @staticmethod
    def parse_email_list(text: str) -> List[str]:
        """Parse a text input containing multiple email addresses."""
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
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        for email in emails:
            email = email.strip()
            if email and email not in valid_emails and email_pattern.match(email):
                valid_emails.append(email)
        
        return valid_emails
    
    @staticmethod
    def validate_group_name(group_name: str) -> tuple[bool, str]:
        """Validate a group name and return (is_valid, error_message)."""
        if not group_name:
            return False, "Group name is required"
        
        # Check for valid characters (letters, numbers, hyphens, underscores, periods)
        if not re.match(r'^[a-zA-Z0-9.\-_@]+$', group_name):
            return False, "Group name can only contain letters, numbers, periods, hyphens, underscores, and @ symbol"
        
        return True, ""
