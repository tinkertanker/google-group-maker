"""
Settings page for Google Group Maker Streamlit app.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any

from config_utils import (
    get_env, set_env, save_credentials_file, 
    validate_config, credentials_exist,
    get_service_account_credentials, format_credentials_for_secrets,
    save_credentials_to_local_secrets
)
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import (
    SUCCESS_MESSAGES, ERROR_MESSAGES, CREDENTIALS_WARNING,
    CLOUD_SECRETS_INSTRUCTIONS
)
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
    
    # Show current credentials status
    creds, source = get_service_account_credentials()
    
    if creds:
        if source == "secrets":
            st.success("✅ Using Streamlit Secrets (Cloud-ready)")
        elif source == "file":
            st.warning("⚠️ Using local file (migrate to secrets for cloud deployment)")
    else:
        st.error("❌ No credentials configured")
    
    # Tabbed interface for different configuration methods
    tab1, tab2 = st.tabs(["☁️ Streamlit Secrets (Recommended)", "💾 Local File (Development)"])
    
    with tab1:
        _render_secrets_tab()
    
    with tab2:
        _render_file_tab()
    
    # Show credentials warning at the bottom
    st.info(CREDENTIALS_WARNING)


def _render_secrets_tab() -> None:
    """Render the Streamlit Secrets configuration tab."""
    st.markdown("**Recommended for Streamlit Cloud and local development**")
    
    # Show current secrets info if available
    creds, source = get_service_account_credentials()
    if creds and source == "secrets":
        st.success("Current secrets configuration:")
        _render_credentials_preview(creds)
    
    st.markdown("---")
    st.markdown("**Upload credentials to configure secrets:**")
    
    uploaded_file = st.file_uploader(
        "Upload service account JSON file",
        type=['json'],
        help="Upload your service-account-credentials.json file",
        key="secrets_upload"
    )
    
    if uploaded_file:
        try:
            # Parse and validate JSON
            file_contents = uploaded_file.getvalue()
            creds_dict = json.loads(file_contents.decode())
            
            st.success("✅ Valid JSON detected")
            _render_credentials_preview(creds_dict)
            
            # Format as TOML
            try:
                toml_snippet = format_credentials_for_secrets(creds_dict)
                
                st.markdown("**TOML Configuration:**")
                st.code(toml_snippet, language="toml")
                
                # Copy button for cloud deployment (with compatibility fallback)
                if hasattr(st, 'copy_button'):
                    st.copy_button(
                        label="📋 Copy for Streamlit Cloud",
                        data=toml_snippet,
                        help="Copy this TOML configuration to paste into Streamlit Cloud secrets"
                    )
                else:
                    st.info("💡 Copy the TOML configuration above manually, or use the download button below")
                    st.download_button(
                        label="⬇️ Download TOML Configuration",
                        data=toml_snippet,
                        file_name="secrets.toml",
                        mime="text/plain",
                        help="Download the TOML configuration file"
                    )
                
                # Save to local secrets button
                if st.button("💾 Save to Local Secrets (.streamlit/secrets.toml)", type="primary"):
                    try:
                        path = save_credentials_to_local_secrets(creds_dict)
                        show_success(SUCCESS_MESSAGES["credentials_saved_secrets"])
                        st.rerun()
                    except ValueError as e:
                        show_error(str(e))
                    except Exception as e:
                        show_error(f"{ERROR_MESSAGES['secrets_write_failed']} {e}")
                
                # Show cloud setup instructions
                with st.expander("📋 How to configure Streamlit Cloud"):
                    st.markdown(CLOUD_SECRETS_INSTRUCTIONS)
                    
            except ValueError as e:
                show_error(f"Invalid credentials: {e}")
                
        except json.JSONDecodeError as e:
            show_error(f"{ERROR_MESSAGES['invalid_json']}: {e}")
        except Exception as e:
            show_error(f"Error processing file: {e}")


def _render_file_tab() -> None:
    """Render the local file configuration tab."""
    st.warning("⚠️ **Development only** - File-based credentials won't persist on Streamlit Cloud")
    
    # Check if file exists
    if credentials_exist():
        creds, source = get_service_account_credentials()
        if source == "file":
            st.info("✅ Credentials file found: `service-account-credentials.json`")
    
    st.markdown("**Upload credentials file:**")
    
    uploaded_file = st.file_uploader(
        "Upload new service account credentials",
        type=['json'],
        help="Upload your service-account-credentials.json file",
        key="file_upload"
    )
    
    if uploaded_file:
        try:
            # Validate and show preview
            file_contents = uploaded_file.getvalue()
            creds_dict = json.loads(file_contents.decode())
            
            st.success("✅ Valid JSON detected")
            _render_credentials_preview(creds_dict)
            
            if st.button("💾 Save Credentials File", type="primary"):
                try:
                    save_credentials_file(file_contents)
                    show_success(SUCCESS_MESSAGES["credentials_saved_file"])
                    st.rerun()
                except ValueError as e:
                    show_error(f"Invalid credentials: {e}")
                    
        except json.JSONDecodeError as e:
            show_error(f"{ERROR_MESSAGES['invalid_json']}: {e}")
        except Exception as e:
            show_error(f"Error processing file: {e}")


def _render_credentials_preview(creds: Dict[str, Any]) -> None:
    """Render a preview of credentials showing safe fields only.
    
    Args:
        creds: Credentials dictionary
    """
    with st.expander("Preview credentials (safe fields only)"):
        st.write(f"**Type**: {creds.get('type', 'N/A')}")
        st.write(f"**Project ID**: {creds.get('project_id', 'N/A')}")
        st.write(f"**Client Email**: {creds.get('client_email', 'N/A')}")


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