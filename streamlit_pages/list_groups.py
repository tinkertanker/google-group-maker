"""
List Groups page for Google Group Maker Streamlit app.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict

from config_utils import get_env
from streamlit_utils.state_manager import StateManager
from streamlit_utils.cache import cached_list_groups, clear_group_cache
from streamlit_components.common import action_buttons
from web_utils import GroupMakerAPI


def render_list_groups(api: GroupMakerAPI) -> None:
    """Render the list groups page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("📋 List Groups")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        query = st.text_input("🔍 Search groups", placeholder="Enter search term...")
    
    with col2:
        env = get_env()
        domain = st.text_input("Domain", value=env.get("GOOGLE_GROUP_DOMAIN", ""))
    
    with col3:
        st.write("")  # Spacing
        if st.button("🔄 Refresh", use_container_width=True):
            clear_group_cache()
            StateManager.clear_caches()
            st.rerun()
    
    # Load and display groups
    groups = cached_list_groups(
        api,
        query=query if query else None,
        domain=domain if domain else None
    )
    
    if groups is not None:
        _display_groups(groups)
    else:
        st.error("Failed to load groups. Please check your configuration and try again.")


def _display_groups(groups: List[Dict[str, str]]) -> None:
    """Display the list of groups.
    
    Args:
        groups: List of group dictionaries
    """
    if len(groups) == 0:
        st.info("📭 No groups found matching your criteria.")
        return
    
    st.success(f"📊 Found {len(groups)} groups")
    
    # Display each group with actions
    for idx, group in enumerate(groups):
        action_clicked, action_type = action_buttons(group, idx)
        
        if action_clicked:
            if action_type == "members":
                StateManager.navigate_to("👥 Group Members")
            elif action_type == "rename":
                StateManager.navigate_to("✏️ Rename Group")
            elif action_type == "delete":
                StateManager.navigate_to("🗑️ Delete Group")