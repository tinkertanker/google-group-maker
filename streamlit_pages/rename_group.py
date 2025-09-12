"""
Rename Group page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, RENAME_WARNING
from streamlit_utils.cache import clear_all_caches
from streamlit_components.common import (
    group_selector, run_with_spinner, show_success, show_error
)
from web_utils import GroupMakerAPI


def render_rename_group(api: GroupMakerAPI) -> None:
    """Render the rename group page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("✏️ Rename Group")
    
    with st.form("rename_group_form"):
        # Current group
        old_group_name = group_selector(
            key="rename_old_group",
            label="Current Group",
            required=True
        )
        
        # New name
        new_group_name = st.text_input(
            "New Group Name *",
            placeholder="new-group-name",
            help="Enter just the name part (without @domain) or full email address"
        )
        
        # Preview
        if old_group_name and new_group_name:
            preview = _get_preview_name(old_group_name, new_group_name)
            st.info(f"**Preview:** {old_group_name} → {preview}")
        
        st.warning(RENAME_WARNING)
        
        submitted = st.form_submit_button("✏️ Rename Group", use_container_width=True)
        
        if submitted:
            _handle_rename_group(api, old_group_name, new_group_name)


def _get_preview_name(old_group_name: str, new_group_name: str) -> str:
    """Get preview of the new group name.
    
    Args:
        old_group_name: Current group name/email
        new_group_name: New group name
        
    Returns:
        Preview of the new full email
    """
    if "@" not in new_group_name and "@" in old_group_name:
        domain = old_group_name.split("@")[1]
        return f"{new_group_name}@{domain}"
    return new_group_name


def _handle_rename_group(api: GroupMakerAPI,
                        old_group_name: str,
                        new_group_name: str) -> None:
    """Handle group renaming.
    
    Args:
        api: GroupMakerAPI instance
        old_group_name: Current group name
        new_group_name: New group name
    """
    # Validation
    if not old_group_name:
        show_error("Current group name is required")
        return
    
    if not new_group_name:
        show_error("New group name is required")
        return
    
    is_valid, error_msg = api.validate_group_name(new_group_name)
    if not is_valid:
        show_error(error_msg)
        return
    
    # Rename the group
    result = run_with_spinner(
        api.rename_group,
        f"Renaming group {old_group_name}...",
        old_group_name,
        new_group_name
    )
    
    if result:
        show_success(SUCCESS_MESSAGES["group_renamed"].format(new_name=new_group_name))
        clear_all_caches()
        StateManager.clear_caches()
        StateManager.clear_selected_group()