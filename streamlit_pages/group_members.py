"""
Group Members page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional, List, Dict

from streamlit_utils.state_manager import StateManager
from streamlit_utils.cache import cached_list_members, clear_member_cache
from streamlit_components.common import (
    group_selector, member_display, export_members_section,
    show_warning
)
from web_utils import GroupMakerAPI


def render_group_members(api: GroupMakerAPI) -> None:
    """Render the group members page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("👥 Group Members")
    
    # Group selection
    group_email = group_selector(key="members_group_selector", required=True)
    
    if not group_email:
        show_warning("Please select or enter a group email address.")
        return
    
    if StateManager.get_selected_group():
        st.info(f"Viewing members of: **{group_email}**")
    
    # Controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        include_derived = st.checkbox("Include nested group members")
    
    with col2:
        if st.button("🔄 Refresh Members"):
            clear_member_cache(group_email)
            StateManager.clear_members_cache(group_email)
            st.rerun()
    
    # Load and display members
    members = cached_list_members(
        api,
        group_email,
        include_derived
    )
    
    if members is not None:
        _display_members(members, group_email)
    else:
        st.error("Failed to load members. Please check the group email and try again.")


def _display_members(members: List[Dict[str, str]], group_email: str) -> None:
    """Display group members.
    
    Args:
        members: List of member dictionaries
        group_email: Email of the group
    """
    if len(members) == 0:
        st.info("👤 No members found in this group.")
        return
    
    # Display members with summary
    member_display(members)
    
    # Export section
    export_members_section(members, group_email)