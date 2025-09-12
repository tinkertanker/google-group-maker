"""
Settings page for Google Group Maker Streamlit app.
"""

import streamlit as st
import json
from typing import Optional

from config_utils import (
    get_env, set_env, save_credentials_file, 
    validate_config, credentials_exist
)
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, ERROR_MESSAGES, CREDENTIALS_WARNING
from streamlit_components.common import run_with_spinner, show_success, show_error
from web_utils import GroupMakerAPI


def render_settings(api: GroupMakerAPI) -> None:
    """Render the settings page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("⚙️ Settings")
    
    # Environment variables section
    _render_environment_settings()
    
    st.markdown("---")
    
    # Service account credentials section
    _render_credentials_settings()
    
    st.markdown("---")
    
    # Authentication test section
    _render_authentication_test(api)


def _render_environment_settings() -> None:
    """Render the environment configuration section."""
    st.subheader("🔧 Environment Configuration")
    
    current_env = get_env()
    
    with st.form("env_settings_form"):
        default_email = st.text_input(
            "DEFAULT_EMAIL *",
            value=current_env.get("DEFAULT_EMAIL", ""),
            help="Your email address (required)"
        )
        
        google_group_domain = st.text_input(
            "GOOGLE_GROUP_DOMAIN",
            value=current_env.get("GOOGLE_GROUP_DOMAIN", ""),
            placeholder="tinkertanker.com",
            help="Default domain for groups (optional)"
        )
        
        admin_email = st.text_input(
            "ADMIN_EMAIL",
            value=current_env.get("ADMIN_EMAIL", ""),
            placeholder="Uses DEFAULT_EMAIL if not set",
            help="Admin email for authentication (optional)"
        )
        
        if st.form_submit_button("💾 Save Environment Settings"):
            new_env = {
                "DEFAULT_EMAIL": default_email,
                "GOOGLE_GROUP_DOMAIN": google_group_domain,
                "ADMIN_EMAIL": admin_email
            }
            
            try:
                set_env(new_env)
                show_success(SUCCESS_MESSAGES["settings_saved"])
                st.rerun()
            except Exception as e:
                show_error(f"Failed to save settings: {e}")


def _render_credentials_settings() -> None:
    """Render the service account credentials section."""
    st.subheader("🔐 Service Account Credentials")
    
    if credentials_exist():
        st.success("✅ Credentials file found: `service-account-credentials.json`")
    else:
        st.error("❌ Credentials file not found")
    
    uploaded_file = st.file_uploader(
        "Upload new service account credentials",
        type=['json'],
        help="Upload your service-account-credentials.json file"
    )
    
    if uploaded_file:
        try:
            # Validate and show save button
            file_contents = uploaded_file.getvalue()
            
            # Try to parse and validate
            try:
                json_data = json.loads(file_contents.decode())
                
                # Show preview of credentials (safe fields only)
                st.success("✅ Valid JSON detected")
                with st.expander("Preview credentials (safe fields)"):
                    st.write(f"**Type**: {json_data.get('type', 'N/A')}")
                    st.write(f"**Project ID**: {json_data.get('project_id', 'N/A')}")
                    st.write(f"**Client Email**: {json_data.get('client_email', 'N/A')}")
                
                if st.button("💾 Save Credentials File"):
                    try:
                        save_credentials_file(file_contents)
                        show_success(SUCCESS_MESSAGES["credentials_saved"])
                        st.rerun()
                    except ValueError as e:
                        show_error(f"Invalid credentials: {e}")
                        
            except json.JSONDecodeError as e:
                st.error(f"{ERROR_MESSAGES['invalid_json']}: {e}")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
    
    st.warning(CREDENTIALS_WARNING)


def _render_authentication_test(api: GroupMakerAPI) -> None:
    """Render the authentication test section.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.subheader("🧪 Test Authentication")
    
    current_env = get_env()
    
    if st.button("🔍 Test Connection"):
        if not credentials_exist():
            show_error(ERROR_MESSAGES["no_credentials"])
        elif not current_env.get("DEFAULT_EMAIL"):
            show_error(ERROR_MESSAGES["no_default_email"])
        else:
            result = run_with_spinner(api.ping_auth, "Testing authentication...")
            if result:
                show_success("✅ Authentication successful! You can now use all features.")
            else:
                show_error("❌ Authentication failed. Check your credentials and configuration.")