"""
Configuration utilities for Google Group Maker Streamlit app.

Handles environment variables and service account credentials.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv, set_key, unset_key
import json

# Try to import TOML parser (tomllib in Python 3.11+, tomli as fallback)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from streamlit_utils.credentials_loader import (
    CredentialsLoader,
    CredentialValidationError,
    SECRETS_KEY,
    SECRETS_FILE_LOCAL,
    CREDENTIALS_FILE
)

ENV_FILE = Path(".env")
ENV_KEYS = ["DEFAULT_EMAIL", "GOOGLE_GROUP_DOMAIN", "ADMIN_EMAIL"]

def load_env():
    """Load environment variables from .env file and Streamlit secrets.
    
    Priority order:
    1. Existing OS environment variables (highest - not overridden)
    2. Streamlit secrets ([env] section or top-level keys)
    3. .env file (local development)
    """
    # First load from .env file (local development)
    # override=False means it won't override existing OS env vars
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)
    
    # Then check Streamlit secrets for any missing values (cloud deployment)
    try:
        import streamlit as st
        
        if hasattr(st, 'secrets'):
            # Try [env] section first (recommended structure)
            if 'env' in st.secrets:
                # Convert to plain dict to ensure we can use .get() safely
                env_section = dict(st.secrets['env'])
                for key in ENV_KEYS:
                    # Only set if not already in environment or empty
                    if key not in os.environ or not os.environ[key]:
                        value = env_section.get(key)
                        # Ensure value exists and coerce to string
                        if value is not None and str(value).strip():
                            os.environ[key] = str(value)
            
            # Also check top-level keys as fallback
            # (for backwards compatibility or simpler configs)
            for key in ENV_KEYS:
                if key not in os.environ or not os.environ[key]:
                    if key in st.secrets:
                        value = st.secrets[key]
                        # Ensure value exists and coerce to string
                        if value is not None and str(value).strip():
                            os.environ[key] = str(value)
                        
    except ImportError:
        # Streamlit not available (CLI usage)
        pass
    except Exception:
        # Error accessing secrets, silently continue
        # (don't break the app if secrets are misconfigured)
        pass

def get_env():
    """Get all configuration environment variables."""
    return {k: os.getenv(k, "") for k in ENV_KEYS}

def set_env(values):
    """Set environment variables and persist to .env file."""
    ENV_FILE.touch(exist_ok=True)
    for k, v in values.items():
        if k in ENV_KEYS:
            if v and v.strip():
                set_key(str(ENV_FILE), k, v.strip())
                os.environ[k] = v.strip()
            else:
                # Remove empty values
                unset_key(str(ENV_FILE), k)
                if k in os.environ:
                    del os.environ[k]

def get_credentials_path():
    """Get the path to the service account credentials file."""
    return CREDENTIALS_FILE

def validate_service_account_dict(creds: Dict[str, Any]) -> None:
    """Validate service account credentials dictionary.

    Delegates to CredentialsLoader for validation and raises ValueError
    for backwards compatibility with existing callers.

    Args:
        creds: Credentials dictionary to validate

    Raises:
        ValueError: If credentials are invalid
    """
    errors = CredentialsLoader.validate_credentials(creds)

    if errors:
        # Format errors into a single message for ValueError
        error_messages = []
        for error in errors:
            msg = f"{error['field']}: {error['issue']}"
            if error.get('hint'):
                msg += f" ({error['hint']})"
            error_messages.append(msg)

        raise ValueError("; ".join(error_messages))

def _format_toml_section(name: str, values: Dict[str, Any]) -> str:
    """Format a dictionary as a TOML section.

    Args:
        name: Section name (e.g., 'google_service_account')
        values: Dictionary of key-value pairs to format

    Returns:
        TOML-formatted string for the section
    """
    lines = [f"[{name}]"]

    # Format each field
    for key, value in values.items():
        if isinstance(value, str):
            # Use multiline string for private key if it contains newlines
            if key == 'private_key' and '\n' in value:
                # Multiline basic string
                lines.append(f'{key} = """')
                lines.append(value.rstrip())  # Remove trailing whitespace
                lines.append('"""')
            else:
                # Single-line basic string - escape backslashes and quotes
                escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
                lines.append(f'{key} = "{escaped_value}"')
        elif isinstance(value, bool):
            lines.append(f'{key} = {str(value).lower()}')
        elif isinstance(value, (int, float)):
            lines.append(f'{key} = {value}')
        else:
            # For other types, use JSON representation
            lines.append(f'{key} = {json.dumps(value)}')

    return '\n'.join(lines)

def get_service_account_credentials() -> Tuple[Optional[Dict[str, Any]], str, Dict[str, Any]]:
    """Get service account credentials from available sources.

    Delegates to CredentialsLoader which tries sources in priority order:
    1. Streamlit runtime secrets
    2. Local .streamlit/secrets.toml
    3. service-account-credentials.json file

    Returns:
        Tuple of (credentials_dict, source, metadata) where:
        - credentials_dict: Valid credentials or None if not found/invalid
        - source: "runtime_secrets", "local_secrets", "file", or "none"
        - metadata: Dict with "errors", "source_detail", "validation_errors" keys
    """
    return CredentialsLoader.get_credentials()

def prepare_credentials_for_cli_env() -> Dict[str, str]:
    """Prepare environment variables with credentials for CLI subprocess.

    Delegates to CredentialsLoader for credential retrieval and serialization.

    Returns:
        Dict of environment variables to pass to subprocess

    Raises:
        ValueError: If no valid credentials found
    """
    creds, source, metadata = CredentialsLoader.get_credentials()

    if creds is None:
        # Format error message from metadata
        errors = metadata.get("errors", []) + metadata.get("validation_errors", [])
        if errors:
            error_messages = [f"{e.get('field', 'Unknown')}: {e.get('issue', 'Unknown issue')}"
                            for e in errors]
            raise ValueError("; ".join(error_messages))
        else:
            raise ValueError("No valid service account credentials found")

    try:
        env_vars = CredentialsLoader.prepare_cli_env(creds)
    except CredentialValidationError as e:
        raise ValueError(str(e))

    # Map loader sources back to legacy format for backwards compatibility
    # "runtime_secrets" and "local_secrets" both map to "secrets"
    if source in ["runtime_secrets", "local_secrets"]:
        legacy_source = "secrets"
    elif source == "file":
        legacy_source = "file"
    else:
        legacy_source = "none"

    env_vars["GOOGLE_SERVICE_ACCOUNT_SOURCE"] = legacy_source

    return env_vars

def format_credentials_for_secrets(creds: Dict[str, Any]) -> str:
    """Format credentials as TOML snippet for Streamlit secrets.

    Args:
        creds: Credentials dictionary

    Returns:
        TOML-formatted string

    Raises:
        ValueError: If credentials are invalid
    """
    validate_service_account_dict(creds)
    return _format_toml_section(SECRETS_KEY, creds)

def save_credentials_to_local_secrets(creds: Dict[str, Any]) -> Path:
    """Save credentials to local .streamlit/secrets.toml file.

    Preserves other secrets that may exist in the file. Only updates
    the google_service_account section.

    Args:
        creds: Credentials dictionary

    Returns:
        Path to the saved secrets file

    Raises:
        ValueError: If credentials are invalid or TOML parser unavailable
    """
    validate_service_account_dict(creds)

    # Check if TOML parser is available
    if tomllib is None:
        raise ValueError(
            "TOML parser not available. Please install tomli: pip install tomli"
        )

    # Ensure .streamlit directory exists
    SECRETS_FILE_LOCAL.parent.mkdir(exist_ok=True)

    # Load existing secrets if file exists
    existing_secrets = {}
    if SECRETS_FILE_LOCAL.exists():
        try:
            with open(SECRETS_FILE_LOCAL, 'rb') as f:
                existing_secrets = tomllib.load(f)
        except Exception:
            # If we can't parse existing file, we'll overwrite it
            pass

    # Update the google_service_account section
    existing_secrets[SECRETS_KEY] = creds

    # Build complete TOML content
    toml_lines = []
    for section_name, section_values in existing_secrets.items():
        if toml_lines:
            toml_lines.append('')  # Blank line between sections
        toml_lines.append(_format_toml_section(section_name, section_values))

    toml_content = '\n'.join(toml_lines)

    # Write to file
    SECRETS_FILE_LOCAL.write_text(toml_content)
    return SECRETS_FILE_LOCAL

def credentials_exist():
    """Check if service account credentials are available from any source."""
    creds, source, metadata = get_service_account_credentials()
    return creds is not None

def save_credentials_file(bytes_data):
    """Save service account credentials to the standard location.
    
    Args:
        bytes_data: Raw bytes of the credentials file
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: If credentials are invalid
    """
    # Parse and validate JSON structure
    try:
        creds = json.loads(bytes_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    # Validate using shared validation function
    validate_service_account_dict(creds)
    
    # Save the validated credentials
    path = get_credentials_path()
    path.write_bytes(bytes_data)
    return path

def validate_config():
    """Validate the current configuration and return issues."""
    issues = []
    env = get_env()
    
    # Required fields
    if not env.get("DEFAULT_EMAIL"):
        issues.append("DEFAULT_EMAIL is required")
    
    # Optional but recommended fields
    if not env.get("GOOGLE_GROUP_DOMAIN"):
        issues.append("GOOGLE_GROUP_DOMAIN is recommended (will use default: tinkertanker.com)")
    
    # Credentials (from any source)
    if not credentials_exist():
        issues.append("Service account credentials not configured")
    
    return issues

def get_config_summary():
    """Get a summary of the current configuration for display."""
    env = get_env()

    # Get credentials info with new signature
    creds, source, metadata = get_service_account_credentials()

    if creds:
        creds_status = "Present"

        # Map sources to user-friendly labels
        if source == "runtime_secrets":
            creds_source = "Streamlit Runtime Secrets"
        elif source == "local_secrets":
            creds_source = "Local Secrets File"
        elif source == "file":
            creds_source = "Local JSON File"
        else:
            creds_source = "Unknown"

        # Check if there were validation warnings in metadata
        validation_errors = metadata.get("validation_errors", [])
        if validation_errors:
            creds_status = "Present (validation issues)"

    else:
        creds_status = "Missing"
        creds_source = "Not configured"

        # Show why credentials are missing from metadata
        errors = metadata.get("errors", [])
        if errors:
            # Take first error as hint
            first_error = errors[0]
            hint = first_error.get("hint", "")
            if hint:
                creds_source = f"Not configured ({hint})"

    return {
        "DEFAULT_EMAIL": env.get("DEFAULT_EMAIL", "Not set"),
        "GOOGLE_GROUP_DOMAIN": env.get("GOOGLE_GROUP_DOMAIN") or "tinkertanker.com (default)",
        "ADMIN_EMAIL": env.get("ADMIN_EMAIL") or env.get("DEFAULT_EMAIL", "Not set"),
        "Credentials": creds_status,
        "Credentials Source": creds_source,
    }
