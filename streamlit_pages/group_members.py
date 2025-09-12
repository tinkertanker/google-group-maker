"""
Group Members page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional, List, Dict

from streamlit_utils.state_manager import StateManager
from streamlit_utils.cache import cached_list_members, clear_member_cache, clear_all_caches
from streamlit_components.common import (
    group_selector, member_display, export_members_section,
    show_warning, show_error, show_success
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
    
    # Group management actions
    st.markdown("### 🔧 Group Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Members", use_container_width=True):
            clear_member_cache(group_email)
            StateManager.clear_members_cache(group_email)
            st.rerun()
    
    with col2:
        if st.button("👤 Add Members", use_container_width=True):
            StateManager.set_selected_group(group_email)
            StateManager.navigate_to("👤 Add Members")
    
    with col3:
        if st.button("✏️ Rename Group", use_container_width=True):
            StateManager.set_selected_group(group_email)
            StateManager.navigate_to("✏️ Rename Group")
    
    with col4:
        # Delete button with confirmation
        if st.button("🗑️ Delete Group", use_container_width=True, type="secondary"):
            StateManager.set("delete_confirm_required", True)
            StateManager.set("group_to_delete", group_email)
    
    # Show delete confirmation if requested
    if StateManager.get("delete_confirm_required") and StateManager.get("group_to_delete") == group_email:
        st.markdown("---")
        st.error(f"⚠️ **Are you sure you want to delete {group_email}?**")
        st.warning("This action cannot be undone!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete", use_container_width=True, type="primary"):
                # Navigate to delete page with group pre-selected
                StateManager.set_selected_group(group_email)
                StateManager.set("delete_confirm_required", False)
                StateManager.navigate_to("🗑️ Delete Group")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                StateManager.set("delete_confirm_required", False)
                StateManager.set("group_to_delete", None)
                st.rerun()
    
    st.markdown("---")
    
    # Member display options
    st.markdown("### 👥 Members")
    
    include_derived = st.checkbox("Include nested group members")
    
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
        
        # Offer to add members
        if st.button("➕ Add First Member", use_container_width=True):
            StateManager.set_selected_group(group_email)
            StateManager.navigate_to("👤 Add Members")
        return
    
    # Display members with summary
    member_display(members)
    
    # Export section
    export_members_section(members, group_email)