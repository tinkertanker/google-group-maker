"""
Configuration utilities for Google Group Maker Streamlit app.

Handles environment variables and service account credentials.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key

ENV_FILE = Path(".env")
ENV_KEYS = ["DEFAULT_EMAIL", "GOOGLE_GROUP_DOMAIN", "ADMIN_EMAIL"]

def load_env():
    """Load environment variables from .env file."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)

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

def credentials_exist():
    """Check if service account credentials file exists."""
    return get_credentials_path().exists()

def save_credentials_file(bytes_data):
    """Save service account credentials to the standard location."""
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
    
    # Credentials file
    if not credentials_exist():
        issues.append("Service account credentials file not found (service-account-credentials.json)")
    
    return issues

def get_config_summary():
    """Get a summary of the current configuration for display."""
    env = get_env()
    return {
        "DEFAULT_EMAIL": env.get("DEFAULT_EMAIL", "Not set"),
        "GOOGLE_GROUP_DOMAIN": env.get("GOOGLE_GROUP_DOMAIN") or "tinkertanker.com (default)",
        "ADMIN_EMAIL": env.get("ADMIN_EMAIL") or env.get("DEFAULT_EMAIL", "Not set"),
        "Credentials": "Present" if credentials_exist() else "Missing",
    }
