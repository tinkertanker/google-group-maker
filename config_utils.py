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

ENV_FILE = Path(".env")
ENV_KEYS = ["DEFAULT_EMAIL", "GOOGLE_GROUP_DOMAIN", "ADMIN_EMAIL"]

# Secrets configuration
SECRETS_FILE_LOCAL = Path(".streamlit/secrets.toml")
SECRETS_KEY = "google_service_account"

# Required fields for service account credentials
REQUIRED_FIELDS = ["type", "project_id", "private_key", "client_email"]

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
    return Path("service-account-credentials.json")

def validate_service_account_dict(creds: Dict[str, Any]) -> None:
    """Validate service account credentials dictionary.

    Args:
        creds: Credentials dictionary to validate

    Raises:
        ValueError: If credentials are invalid
    """
    # Check for required fields
    missing_fields = [field for field in REQUIRED_FIELDS if field not in creds]

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate type field
    if creds.get('type') != 'service_account':
        raise ValueError(f"Invalid credentials type: {creds.get('type')}. Expected 'service_account'")

    # Validate private key format
    private_key = creds.get('private_key', '')
    if not isinstance(private_key, str) or not private_key.startswith('-----BEGIN'):
        raise ValueError("Invalid private key format")

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

def _load_credentials_from_runtime_secrets() -> Optional[Dict[str, Any]]:
    """Load credentials from Streamlit runtime secrets.

    Returns:
        Credentials dict if found, None otherwise
    """
    try:
        import streamlit as st

        # Check if secrets are available
        if hasattr(st, 'secrets') and SECRETS_KEY in st.secrets:
            secrets_data = st.secrets[SECRETS_KEY]

            # If it's a string, parse as JSON
            if isinstance(secrets_data, str):
                return json.loads(secrets_data)

            # Otherwise, convert to dict (Streamlit secrets might be dict-like)
            return dict(secrets_data)

    except ImportError:
        # Streamlit not available
        pass
    except Exception:
        # Error accessing secrets
        pass

    return None

def _load_credentials_from_local_secrets() -> Optional[Dict[str, Any]]:
    """Load credentials from local .streamlit/secrets.toml file.

    Returns:
        Credentials dict if found, None otherwise
    """
    if not SECRETS_FILE_LOCAL.exists():
        return None

    if tomllib is None:
        # TOML parser not available
        return None

    try:
        with open(SECRETS_FILE_LOCAL, 'rb') as f:
            data = tomllib.load(f)

        if SECRETS_KEY in data:
            return dict(data[SECRETS_KEY])

    except Exception:
        # Error reading or parsing TOML
        pass

    return None

def _load_credentials_from_file() -> Optional[Dict[str, Any]]:
    """Load credentials from service-account-credentials.json file.

    Returns:
        Credentials dict if found, None otherwise
    """
    path = get_credentials_path()

    if not path.exists():
        return None

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        # Error reading or parsing JSON
        return None

def get_service_account_credentials() -> Tuple[Optional[Dict[str, Any]], str]:
    """Get service account credentials from available sources.

    Tries sources in priority order:
    1. Streamlit runtime secrets
    2. Local .streamlit/secrets.toml
    3. service-account-credentials.json file

    Returns:
        Tuple of (credentials_dict, source) where source is:
        - "secrets" (runtime or local secrets file)
        - "file" (JSON file)
        - "none" (no credentials found)
    """
    # Try runtime secrets first
    creds = _load_credentials_from_runtime_secrets()
    if creds:
        try:
            validate_service_account_dict(creds)
            return creds, "secrets"
        except ValueError:
            # Invalid credentials in secrets
            pass

    # Try local secrets file
    creds = _load_credentials_from_local_secrets()
    if creds:
        try:
            validate_service_account_dict(creds)
            return creds, "secrets"
        except ValueError:
            # Invalid credentials in local secrets
            pass

    # Fall back to JSON file
    creds = _load_credentials_from_file()
    if creds:
        try:
            validate_service_account_dict(creds)
            return creds, "file"
        except ValueError:
            # Invalid credentials in file
            pass

    return None, "none"

def prepare_credentials_for_cli_env() -> Dict[str, str]:
    """Prepare environment variables with credentials for CLI subprocess.

    Returns:
        Dict of environment variables to pass to subprocess

    Raises:
        ValueError: If no valid credentials found
    """
    creds, source = get_service_account_credentials()

    if creds is None:
        raise ValueError("No valid service account credentials found")

    # Serialize credentials to JSON string
    json_str = json.dumps(creds)

    return {
        "GOOGLE_SERVICE_ACCOUNT_JSON": json_str,
        "GOOGLE_SERVICE_ACCOUNT_SOURCE": source
    }

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
    creds, _ = get_service_account_credentials()
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

    # Get credentials info
    creds, source = get_service_account_credentials()

    if creds:
        creds_status = "Present"
        if source == "secrets":
            creds_source = "Streamlit Secrets"
        elif source == "file":
            creds_source = "Local File"
        else:
            creds_source = "Unknown"
    else:
        creds_status = "Missing"
        creds_source = "Not configured"
    
    return {
        "DEFAULT_EMAIL": env.get("DEFAULT_EMAIL", "Not set"),
        "GOOGLE_GROUP_DOMAIN": env.get("GOOGLE_GROUP_DOMAIN") or "tinkertanker.com (default)",
        "ADMIN_EMAIL": env.get("ADMIN_EMAIL") or env.get("DEFAULT_EMAIL", "Not set"),
        "Credentials": creds_status,
        "Credentials Source": creds_source,
    }
