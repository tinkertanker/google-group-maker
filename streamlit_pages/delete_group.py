"""
Delete Group page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, DELETE_WARNING
from streamlit_utils.cache import clear_all_caches
from streamlit_components.common import (
    group_selector, run_with_spinner, show_success, show_error
)
from web_utils import GroupMakerAPI


def render_delete_group(api: GroupMakerAPI) -> None:
    """Render the delete group page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("🗑️ Delete Group")
    
    st.warning("⚠️ **DANGER ZONE** - This action cannot be undone!")
    
    # Check if we just deleted a group (using session state)
    if StateManager.get("delete_success"):
        group_deleted = StateManager.get("deleted_group_email", "")
        show_success(SUCCESS_MESSAGES["group_deleted"].format(group_email=group_deleted))
        
        # Clear the success flag
        StateManager.set("delete_success", False)
        StateManager.set("deleted_group_email", None)
        
        # Show navigation button (outside form!)
        if st.button("📋 Back to Group List", use_container_width=True):
            StateManager.navigate_to("📋 List Groups")
        
        st.markdown("---")
        st.info("You can also delete another group below:")
    
    with st.form("delete_group_form", clear_on_submit=False):
        # Group selection
        group_email = group_selector(
            key="delete_group_selector",
            label="Group to Delete",
            required=True
        )
        
        # Show warning with proper formatting
        if group_email:
            # Use markdown for better formatting
            st.markdown(f"""
            <div style='background-color: #8B0000; padding: 1rem; border-radius: 0.5rem; color: white;'>
            <strong>You are about to permanently delete: {group_email}</strong>
            <br><br>
            This will:
            <ul>
            <li>Remove all members from the group</li>
            <li>Delete all group content and history</li>
            <li>Make the group email address unusable</li>
            <li>Cannot be undone</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Please select a group to delete")
        
        # Double confirmation
        confirm1 = st.checkbox(
            "I understand this action is permanent and cannot be undone",
            key="delete_confirm1"
        )
        
        confirm2 = st.text_input(
            "Type the group email to confirm deletion:",
            placeholder=group_email or "group-name@domain.com",
            key="delete_confirm2"
        )
        
        # Show confirmation status (for user feedback)
        if group_email:
            col1, col2 = st.columns(2)
            with col1:
                if confirm1:
                    st.success("✓ Confirmation 1")
                else:
                    st.info("☐ Check the box above")
            with col2:
                if confirm2 == group_email:
                    st.success("✓ Email matches")
                elif confirm2:
                    st.error("✗ Email doesn't match")
                else:
                    st.info("☐ Type the email above")
        
        # Submit button (always enabled, validation happens on submit)
        submitted = st.form_submit_button(
            "🗑️ PERMANENTLY DELETE GROUP",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validate on submission
            delete_enabled = (
                confirm1 and 
                confirm2 == group_email and 
                group_email and
                len(group_email) > 0
            )
            
            if not delete_enabled:
                show_error("Please complete all confirmation steps:\n1. Select a group\n2. Check the confirmation box\n3. Type the exact group email")
            else:
                # Perform deletion
                result = run_with_spinner(
                    api.delete_group,
                    f"Deleting group {group_email}...",
                    group_email
                )
                
                if result:
                    # Clear caches
                    clear_all_caches()
                    StateManager.clear_caches()
                    StateManager.clear_selected_group()
                    
                    # Store success state and rerun to show success message
                    StateManager.set("delete_success", True)
                    StateManager.set("deleted_group_email", group_email)
                    st.rerun()