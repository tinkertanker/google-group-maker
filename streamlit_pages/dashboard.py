"""
Dashboard page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional

from config_utils import get_config_summary, validate_config
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import GETTING_STARTED_INFO, SUCCESS_MESSAGES, ERROR_MESSAGES
from streamlit_components.common import run_with_spinner, show_success, show_error
from web_utils import GroupMakerAPI


def render_dashboard(api: GroupMakerAPI) -> None:
    """Render the dashboard page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("🏠 Dashboard")
    
    # Configuration summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _render_configuration_summary()
    
    with col2:
        _render_quick_actions()
    
    st.markdown("---")
    
    # System status
    _render_system_status(api)
    
    # Getting started guide
    st.markdown("---")
    _render_getting_started()


def _render_configuration_summary() -> None:
    """Render the configuration summary section."""
    st.subheader("📊 Configuration Summary")
    config = get_config_summary()
    
    for key, value in config.items():
        if key == "Credentials":
            icon = "✅" if value == "Present" else "❌"
        elif value and value != "Not set":
            icon = "✅"
        else:
            icon = "❌"
        st.write(f"{icon} **{key}**: {value}")


def _render_quick_actions() -> None:
    """Render the quick actions section."""
    st.subheader("🚀 Quick Actions")
    
    if st.button("➕ Create Group", use_container_width=True):
        StateManager.navigate_to("➕ Create Group")
    
    if st.button("📋 List Groups", use_container_width=True):
        StateManager.navigate_to("📋 List Groups")
    
    if st.button("⚙️ Settings", use_container_width=True):
        StateManager.navigate_to("⚙️ Settings")


def _render_system_status(api: GroupMakerAPI) -> None:
    """Render the system status section.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.subheader("🔍 System Status")
    
    if st.button("Test Authentication"):
        result = run_with_spinner(api.ping_auth, "Testing authentication...")
        if result:
            show_success(SUCCESS_MESSAGES["auth_success"])
        else:
            show_error(ERROR_MESSAGES["auth_failed"])


def _render_getting_started() -> None:
    """Render the getting started guide."""
    st.subheader("🚀 Getting Started")
    st.info(GETTING_STARTED_INFO)