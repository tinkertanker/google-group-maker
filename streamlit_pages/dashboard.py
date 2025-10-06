"""
Dashboard page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional

from config_utils import get_config_summary
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, ERROR_MESSAGES
from streamlit_components.common import run_with_spinner, show_success, show_error
from web_utils import GroupMakerAPI


def render_dashboard(api: GroupMakerAPI) -> None:
    """Render the dashboard page.

    Args:
        api: GroupMakerAPI instance
    """
    st.title("🏠 Dashboard")

    # First row: Quick actions
    _render_quick_actions()

    st.markdown("---")

    # Second row: Configuration summary and system status merged
    _render_configuration_and_status(api)


def _render_configuration_and_status(api: GroupMakerAPI) -> None:
    """Render the merged configuration summary and system status section.

    Args:
        api: GroupMakerAPI instance
    """
    col1, col2 = st.columns([2, 1])

    with col1:
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

    with col2:
        st.subheader("🔍 System Status")

        if st.button("Test Authentication", use_container_width=True):
            result = run_with_spinner(api.ping_auth, "Testing authentication...")
            if result:
                show_success(SUCCESS_MESSAGES["auth_success"])
            else:
                show_error(ERROR_MESSAGES["auth_failed"])


def _render_quick_actions() -> None:
    """Render the quick actions section."""
    st.subheader("🚀 Quick Actions")

    # Create columns for all actions
    cols = st.columns(5)

    with cols[0]:
        if st.button("➕ Create Group", use_container_width=True):
            StateManager.navigate_to("➕ Create Group")

    with cols[1]:
        if st.button("📋 List Groups", use_container_width=True):
            StateManager.navigate_to("📋 List Groups")

    with cols[2]:
        if st.button("👥 View Members", use_container_width=True):
            StateManager.navigate_to("👥 View Members")

    with cols[3]:
        if st.button("🗑️ Delete Group", use_container_width=True):
            StateManager.navigate_to("🗑️ Delete Group")

    with cols[4]:
        if st.button("⚙️ Settings", use_container_width=True):
            StateManager.navigate_to("⚙️ Settings")


