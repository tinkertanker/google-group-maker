"""
Credential loading utilities for Google Group Maker.

Provides centralized credential management with structured error reporting
and multiple source support (Streamlit runtime secrets, local secrets file, JSON file).

Priority order for credential sources:
1. Streamlit runtime secrets (st.secrets)
2. Local .streamlit/secrets.toml file
3. service-account-credentials.json file

All loading functions return structured metadata with errors instead of raising
exceptions, allowing callers to handle errors gracefully and provide detailed
user feedback.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json

# TOML parser: tomllib is stdlib from Python 3.11+, tomli is the backport for earlier versions
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

__all__ = [
    'CredentialValidationError',
    'CredentialsLoader',
    'REQUIRED_FIELDS',
    'SECRETS_KEY',
    'SECRETS_FILE_LOCAL',
    'CREDENTIALS_FILE'
]

# Credential configuration constants
REQUIRED_FIELDS = ["type", "project_id", "private_key", "client_email"]
SECRETS_KEY = "google_service_account"
SECRETS_FILE_LOCAL = Path(".streamlit/secrets.toml")
CREDENTIALS_FILE = Path("service-account-credentials.json")


class CredentialValidationError(Exception):
    """Exception raised when credentials validation fails.
    
    Stores structured error information for detailed user feedback.
    
    Attributes:
        errors: List of error dictionaries with 'field', 'issue', 'hint' keys
    """
    
    def __init__(self, errors: List[Dict[str, str]]):
        """Initialize with structured errors.
        
        Args:
            errors: List of error dicts, each with field/issue/hint keys
        """
        self.errors = errors
        super().__init__(self._format_error_message())
    
    def _format_error_message(self) -> str:
        """Format errors into a readable message.
        
        Returns:
            Formatted error message string
        """
        if not self.errors:
            return "Unknown validation error"
        
        messages = []
        for error in self.errors:
            msg = f"{error.get('field', 'Unknown')}: {error.get('issue', 'Unknown issue')}"
            if error.get('hint'):
                msg += f" ({error['hint']})"
            messages.append(msg)
        
        return "; ".join(messages)


class CredentialsLoader:
    """Manages loading and validation of service account credentials from multiple sources."""
    
    @staticmethod
    def validate_credentials(creds: Dict[str, Any]) -> List[Dict[str, str]]:
        """Validate service account credentials dictionary.
        
        Checks for required fields, correct type, and private key format.
        Returns structured errors for detailed user feedback.
        
        Args:
            creds: Credentials dictionary to validate
            
        Returns:
            List of error dictionaries. Empty list if valid.
            Each error dict has keys: 'field', 'issue', 'hint'
        """
        errors = []
        
        # Check for required fields
        for field in REQUIRED_FIELDS:
            if field not in creds:
                errors.append({
                    "field": field,
                    "issue": "Missing required field",
                    "hint": f"Service account credentials must include '{field}'"
                })
        
        # Validate type field
        if creds.get('type') != 'service_account':
            errors.append({
                "field": "type",
                "issue": f"Invalid credentials type: {creds.get('type')}",
                "hint": "Expected 'service_account'"
            })
        
        # Validate private key format
        private_key = creds.get('private_key', '')
        if not isinstance(private_key, str):
            errors.append({
                "field": "private_key",
                "issue": "Private key must be a string",
                "hint": "Ensure private_key is a string value"
            })
        elif not private_key.startswith('-----BEGIN'):
            errors.append({
                "field": "private_key",
                "issue": "Invalid private key format",
                "hint": "Private key must start with '-----BEGIN PRIVATE KEY-----'"
            })
        
        # Validate client_email format
        client_email = creds.get('client_email', '')
        if client_email and '@' not in client_email:
            errors.append({
                "field": "client_email",
                "issue": "Invalid email format",
                "hint": "Client email must be a valid email address"
            })
        
        return errors
    
    @staticmethod
    def _validate_candidate(creds: Optional[Dict[str, Any]], meta: Dict[str, Any]) -> bool:
        """Validate credentials candidate and update metadata.
        
        Helper to avoid duplicating validation logic across sources.
        
        Args:
            creds: Credentials dictionary or None
            meta: Metadata dictionary to update with validation results
            
        Returns:
            True if credentials are valid, False otherwise
        """
        if creds is None:
            meta["validation_errors"] = []
            return False
        
        validation_errors = CredentialsLoader.validate_credentials(creds)
        meta["validation_errors"] = validation_errors
        
        return len(validation_errors) == 0
    
    @staticmethod
    def load_from_runtime_secrets() -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Load credentials from Streamlit runtime secrets (st.secrets).
        
        Attempts to access credentials from Streamlit's runtime secrets system.
        This works in both Streamlit Cloud and local development with secrets configured.
        
        Returns:
            Tuple of (credentials_dict, metadata)
            - credentials_dict: Parsed credentials or None if unavailable
            - metadata: {"errors": [...], "source_detail": str}
        """
        metadata = {
            "errors": [],
            "source_detail": "runtime_secrets"
        }
        
        try:
            import streamlit as st
            
            # Check if secrets are available
            if not hasattr(st, 'secrets'):
                metadata["errors"].append({
                    "field": "runtime",
                    "issue": "Streamlit secrets not available",
                    "hint": "Ensure app is running in Streamlit environment"
                })
                return None, metadata
            
            if SECRETS_KEY not in st.secrets:
                metadata["errors"].append({
                    "field": SECRETS_KEY,
                    "issue": "Credentials key not found in secrets",
                    "hint": f"Add [{SECRETS_KEY}] section to Streamlit secrets"
                })
                return None, metadata
            
            secrets_data = st.secrets[SECRETS_KEY]
            
            # If it's a string, parse as JSON
            if isinstance(secrets_data, str):
                try:
                    creds = json.loads(secrets_data)
                except json.JSONDecodeError as e:
                    metadata["errors"].append({
                        "field": SECRETS_KEY,
                        "issue": f"Invalid JSON in secrets: {e}",
                        "hint": "Ensure credentials are valid JSON format"
                    })
                    return None, metadata
            else:
                # Convert to dict (Streamlit secrets might be dict-like)
                creds = dict(secrets_data)
            
            return creds, metadata
            
        except ImportError:
            metadata["errors"].append({
                "field": "streamlit",
                "issue": "Streamlit not available",
                "hint": "Install streamlit or use file-based credentials"
            })
            return None, metadata
        except Exception as e:
            metadata["errors"].append({
                "field": "runtime",
                "issue": f"Error accessing runtime secrets: {e}",
                "hint": "Check Streamlit secrets configuration"
            })
            return None, metadata
    
    @staticmethod
    def load_from_local_secrets() -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Load credentials from local .streamlit/secrets.toml file.
        
        Reads credentials from the local secrets file (for development).
        Requires tomli/tomllib for TOML parsing.
        
        Returns:
            Tuple of (credentials_dict, metadata)
            - credentials_dict: Parsed credentials or None if unavailable
            - metadata: {"errors": [...], "source_detail": str}
        """
        metadata = {
            "errors": [],
            "source_detail": "local_secrets"
        }
        
        if not SECRETS_FILE_LOCAL.exists():
            metadata["errors"].append({
                "field": "file",
                "issue": f"Local secrets file not found: {SECRETS_FILE_LOCAL}",
                "hint": "Create .streamlit/secrets.toml or use runtime secrets"
            })
            return None, metadata
        
        if tomllib is None:
            metadata["errors"].append({
                "field": "toml_parser",
                "issue": "TOML parser not available",
                "hint": "Install tomli: pip install tomli"
            })
            return None, metadata
        
        try:
            with open(SECRETS_FILE_LOCAL, 'rb') as f:
                data = tomllib.load(f)
            
            if SECRETS_KEY not in data:
                metadata["errors"].append({
                    "field": SECRETS_KEY,
                    "issue": f"[{SECRETS_KEY}] section not found in {SECRETS_FILE_LOCAL}",
                    "hint": f"Add [{SECRETS_KEY}] section to local secrets file"
                })
                return None, metadata
            
            creds = dict(data[SECRETS_KEY])
            return creds, metadata
            
        except Exception as e:
            metadata["errors"].append({
                "field": "file",
                "issue": f"Error reading {SECRETS_FILE_LOCAL}: {e}",
                "hint": "Check file format and permissions"
            })
            return None, metadata
    
    @staticmethod
    def load_from_file() -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Load credentials from service-account-credentials.json file.
        
        Reads credentials from the local JSON file (legacy/development method).
        
        Returns:
            Tuple of (credentials_dict, metadata)
            - credentials_dict: Parsed credentials or None if unavailable
            - metadata: {"errors": [...], "source_detail": str}
        """
        metadata = {
            "errors": [],
            "source_detail": "file"
        }
        
        if not CREDENTIALS_FILE.exists():
            metadata["errors"].append({
                "field": "file",
                "issue": f"Credentials file not found: {CREDENTIALS_FILE}",
                "hint": "Upload credentials file or use Streamlit secrets"
            })
            return None, metadata
        
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
            
            return creds, metadata
            
        except json.JSONDecodeError as e:
            metadata["errors"].append({
                "field": "file",
                "issue": f"Invalid JSON in {CREDENTIALS_FILE}: {e}",
                "hint": "Re-download credentials from Google Cloud Console"
            })
            return None, metadata
        except Exception as e:
            metadata["errors"].append({
                "field": "file",
                "issue": f"Error reading {CREDENTIALS_FILE}: {e}",
                "hint": "Check file permissions"
            })
            return None, metadata
    
    @staticmethod
    def get_credentials() -> Tuple[Optional[Dict[str, Any]], str, Dict[str, Any]]:
        """Get service account credentials from available sources with fallback.

        Tries sources in priority order:
        1. Streamlit runtime secrets (st.secrets)
        2. Local .streamlit/secrets.toml
        3. service-account-credentials.json file

        Only returns credentials that pass validation. If credentials are found
        but invalid, continues to next source.

        Returns:
            Tuple of (credentials_dict, source, metadata) where:
            - credentials_dict: Valid credentials or None if not found/invalid
            - source: "runtime_secrets", "local_secrets", "file", or "none"
            - metadata: {"errors": [...], "source_detail": str, "validation_errors": [...]}
        """
        # Define credential sources in priority order
        sources = [
            (CredentialsLoader.load_from_runtime_secrets, "runtime_secrets"),
            (CredentialsLoader.load_from_local_secrets, "local_secrets"),
            (CredentialsLoader.load_from_file, "file")
        ]

        # Track latest metadata from most recent attempt
        latest_metadata = None

        for loader_fn, source_label in sources:
            creds, meta = loader_fn()

            # Ensure metadata has required defaults
            if "errors" not in meta:
                meta["errors"] = []
            if "validation_errors" not in meta:
                meta["validation_errors"] = []
            if "source_detail" not in meta:
                meta["source_detail"] = source_label

            # Track this attempt's metadata
            latest_metadata = meta

            # Validate and return if successful
            if CredentialsLoader._validate_candidate(creds, meta):
                # Ensure source_detail matches the successful source
                meta["source_detail"] = source_label
                return creds, source_label, meta

        # No credentials found in any source
        # Use latest metadata if available, otherwise create fallback
        if latest_metadata:
            # If no errors were provided, add fallback error
            if not latest_metadata.get("errors") and not latest_metadata.get("validation_errors"):
                latest_metadata["errors"] = [{
                    "field": "credentials",
                    "issue": "No credentials found in any source",
                    "hint": "Upload credentials or configure Streamlit secrets"
                }]

            return None, "none", latest_metadata
        else:
            # Fallback if no loaders were attempted (shouldn't happen)
            return None, "none", {
                "errors": [{
                    "field": "credentials",
                    "issue": "No credentials found in any source",
                    "hint": "Upload credentials or configure Streamlit secrets"
                }],
                "source_detail": "none",
                "validation_errors": []
            }
    
    @staticmethod
    def prepare_cli_env(credentials: Dict[str, Any]) -> Dict[str, str]:
        """Prepare environment variables with credentials for CLI subprocess.
        
        Validates credentials and serializes them to JSON for passing to CLI subprocess
        via environment variables.
        
        Args:
            credentials: Credentials dictionary to serialize
            
        Returns:
            Dict of environment variables to pass to subprocess
            
        Raises:
            CredentialValidationError: If credentials are invalid
        """
        # Validate credentials first
        errors = CredentialsLoader.validate_credentials(credentials)
        if errors:
            raise CredentialValidationError(errors)
        
        # Serialize credentials to JSON string
        json_str = json.dumps(credentials)
        
        return {
            "GOOGLE_SERVICE_ACCOUNT_JSON": json_str
        }