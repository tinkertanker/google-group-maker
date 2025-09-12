"""
Web utilities for Google Group Maker Streamlit app.

Provides a clean Python API for web UI operations with enhanced security.
"""

import re
import subprocess
import sys
import time
import shlex
import os
from typing import List, Dict, Optional, Any, Tuple
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class GroupMakerAPI:
    """API wrapper for Google Group Maker functionality with security enhancements."""
    
    def __init__(self, debug: bool = False, timeout: int = 60):
        """Initialize the API wrapper.
        
        Args:
            debug: Enable debug logging
            timeout: Default timeout in seconds for CLI commands
        """
        self.debug = debug
        self.default_timeout = int(os.environ.get('CLI_TIMEOUT', timeout))
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    def _run_cli(self, args: List[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """Run the CLI command and return success status, stdout, stderr.
        
        Args:
            args: Command arguments (will be properly escaped)
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        # Validate inputs to prevent injection
        validated_args = []
        for arg in args:
            if not isinstance(arg, str):
                arg = str(arg)
            # Convert all arguments to strings for safety
            validated_args.append(arg)
        
        cmd = [sys.executable, "./groupmaker.py"] + validated_args
        
        if self.debug:
            logger.debug(f"Running command: {' '.join(shlex.quote(c) for c in cmd)}")
        
        try:
            proc = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                check=False,  # Don't raise on non-zero exit
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}  # Prevent .pyc files
            )
            return proc.returncode == 0, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds")
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, "", str(e)
    
    def ping_auth(self) -> bool:
        """Test authentication by attempting to list groups.
        
        Returns:
            True if authentication successful
            
        Raises:
            RuntimeError: If authentication fails
        """
        try:
            success, stdout, stderr = self._run_cli(["list", "--max-results", "1"])
            if not success:
                raise RuntimeError(stderr or stdout or "Authentication failed")
            return True
        except Exception:
            raise
    
    def create_group(self, group_name: str, trainer_email: str, domain: Optional[str] = None, 
                     description: str = "", skip_self: bool = False) -> Dict[str, Any]:
        """Create a new Google Group.
        
        Args:
            group_name: Name of the group to create
            trainer_email: Email of the trainer to add
            domain: Optional domain for the group
            description: Optional group description
            skip_self: Whether to skip adding self to group
            
        Returns:
            Dict with success status and message
            
        Raises:
            RuntimeError: If group creation fails
        """
        # Validate inputs
        is_valid, error_msg = self.validate_group_name(group_name)
        if not is_valid:
            raise ValueError(error_msg)
        
        if not self._validate_email(trainer_email):
            raise ValueError(f"Invalid email address: {trainer_email}")
        
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
        """List Google Groups, returning structured data.
        
        Args:
            query: Optional search query
            domain: Optional domain filter
            max_results: Maximum number of results to return
            
        Returns:
            List of group dictionaries
            
        Raises:
            RuntimeError: If listing fails
        """
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
        """List members of a Google Group.
        
        Args:
            group_name: Name or email of the group
            include_derived: Whether to include nested group members
            max_results: Maximum number of results
            
        Returns:
            List of member dictionaries
            
        Raises:
            RuntimeError: If listing fails
        """
        args = ["members", group_name, "--max-results", str(max_results)]
        
        if include_derived:
            args.append("--include-derived")
        
        success, stdout, stderr = self._run_cli(args)
        
        if not success:
            raise RuntimeError(stderr or stdout or "Failed to list members")
        
        return self._parse_members_output(stdout)
    
    def add_member(self, group_name: str, member_email: str, role: str = "MEMBER") -> Dict[str, Any]:
        """Add a single member to a Google Group.
        
        Args:
            group_name: Name or email of the group
            member_email: Email of member to add
            role: Member role (MEMBER, MANAGER, or OWNER)
            
        Returns:
            Dict with success status and message
            
        Raises:
            RuntimeError: If adding member fails
        """
        if not self._validate_email(member_email):
            raise ValueError(f"Invalid email address: {member_email}")
        
        if role not in ["MEMBER", "MANAGER", "OWNER"]:
            raise ValueError(f"Invalid role: {role}")
        
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
        """Rename an existing Google Group.
        
        Args:
            old_group_name: Current name or email of the group
            new_group_name: New name for the group
            
        Returns:
            Dict with success status and message
            
        Raises:
            RuntimeError: If renaming fails
        """
        is_valid, error_msg = self.validate_group_name(new_group_name)
        if not is_valid:
            raise ValueError(error_msg)
        
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
        """Delete a Google Group (bypassing interactive confirmation).
        
        Args:
            group_name: Name or email of the group to delete
            
        Returns:
            Dict with success status and message
            
        Raises:
            RuntimeError: If deletion fails
        """
        # Validate group name to prevent injection
        is_valid, error_msg = self.validate_group_name(group_name)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Use the safe _run_cli method with proper input handling
        args = ["delete", group_name, "--yes"]  # Use --yes flag if available
        
        # First try with --yes flag
        success, stdout, stderr = self._run_cli(args)
        
        if not success and "unrecognized arguments: --yes" in stderr:
            # Fallback to interactive mode with yes input
            cmd = [sys.executable, "./groupmaker.py", "delete", group_name]
            
            try:
                # Use subprocess with proper safety measures
                proc = subprocess.run(
                    cmd, 
                    input="yes\n", 
                    text=True, 
                    capture_output=True, 
                    timeout=self.default_timeout,
                    check=False,
                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                    cwd=None,  # Explicitly set working directory
                    shell=False  # Never use shell=True
                )
                success = proc.returncode == 0
                stdout = proc.stdout
                stderr = proc.stderr
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Command timed out after {self.default_timeout} seconds")
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
        """Parse the groups list output into structured data.
        
        Args:
            output: Raw CLI output
            
        Returns:
            List of group dictionaries
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
    
    def _parse_members_output(self, output: str) -> List[Dict[str, str]]:
        """Parse the members list output into structured data.
        
        Args:
            output: Raw CLI output
            
        Returns:
            List of member dictionaries
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
    
    @classmethod
    def parse_email_list(cls, text: str) -> List[str]:
        """Parse a text input containing multiple email addresses.
        
        Args:
            text: Text containing email addresses
            
        Returns:
            List of valid email addresses
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
            if email and email not in valid_emails and cls._validate_email(email):
                valid_emails.append(email)
        
        return valid_emails
    
    @classmethod
    def validate_group_name(cls, group_name: str) -> Tuple[bool, str]:
        """Validate a group name and return (is_valid, error_message).
        
        Args:
            group_name: Group name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not group_name:
            return False, "Group name is required"
        
        # If it contains @, it should be a full email - validate differently
        if "@" in group_name:
            # This is a full email address, validate as email
            if cls._validate_email(group_name):
                return True, ""
            else:
                return False, "Invalid email format for group"
        
        # For group names (without @), only allow safe characters
        if not re.match(r'^[a-zA-Z0-9.\-_]+$', group_name):
            return False, "Group name can only contain letters, numbers, periods, hyphens, and underscores"
        
        # Check length
        if len(group_name) > 100:
            return False, "Group name must be less than 100 characters"
        
        # Check it doesn't start or end with special characters
        if group_name[0] in '.-_' or group_name[-1] in '.-_':
            return False, "Group name cannot start or end with special characters"
        
        return True, ""
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
        """
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(email.strip()))