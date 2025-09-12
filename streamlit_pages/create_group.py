"""
Create Group page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional

from config_utils import get_env
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, ERROR_MESSAGES
from streamlit_components.common import (
    run_with_spinner, show_success, show_error, 
    format_group_email, domain_input
)
from web_utils import GroupMakerAPI


def render_create_group(api: GroupMakerAPI) -> None:
    """Render the create group page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("➕ Create Group")
    
    # Check if we just created a group (using session state)
    if StateManager.get("create_success"):
        group_created = StateManager.get("created_group_email", "")
        show_success(SUCCESS_MESSAGES["group_created"].format(group_email=group_created))
        
        # Clear the success flag
        StateManager.set("create_success", False)
        StateManager.set("created_group_email", None)
        
        # Show navigation buttons (outside form!)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👥 View Group Members", use_container_width=True):
                StateManager.set_selected_group(group_created)
                StateManager.navigate_to("👥 Group Members")
        with col2:
            if st.button("➕ Create Another Group", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
    
    with st.form("create_group_form", clear_on_submit=True):
        # Group details section
        st.subheader("Group Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            group_name = st.text_input(
                "Group Name *",
                placeholder="e.g., python-class-2023",
                help="Letters, numbers, hyphens, underscores, and periods only"
            )
            
            trainer_email = st.text_input(
                "Trainer Email *",
                placeholder="trainer@example.com",
                help="Email of the external trainer to add to the group"
            )
        
        with col2:
            env = get_env()
            domain = domain_input(
                key="create_domain",
                default_value=env.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com")
            )
            
            description = st.text_area(
                "Description (optional)",
                placeholder="Brief description of the group",
                max_chars=500
            )
        
        # Options section
        st.subheader("Options")
        skip_self = st.checkbox(
            "Skip adding myself to the group",
            help="Don't automatically add your email as a member"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Group", use_container_width=True)
        
        if submitted:
            _handle_create_group(
                api, group_name, trainer_email, 
                domain, description, skip_self
            )


def _handle_create_group(api: GroupMakerAPI, 
                        group_name: str,
                        trainer_email: str,
                        domain: str,
                        description: str,
                        skip_self: bool) -> None:
    """Handle group creation.
    
    Args:
        api: GroupMakerAPI instance
        group_name: Name of the group
        trainer_email: Trainer's email
        domain: Domain for the group
        description: Group description
        skip_self: Whether to skip adding self
    """
    # Validation
    errors = []
    
    if not group_name:
        errors.append(ERROR_MESSAGES["group_name_required"])
    else:
        is_valid, error_msg = api.validate_group_name(group_name)
        if not is_valid:
            errors.append(error_msg)
    
    if not trainer_email or "@" not in trainer_email:
        errors.append(ERROR_MESSAGES["trainer_email_required"])
    
    if not domain:
        errors.append(ERROR_MESSAGES["domain_required"])
    
    if errors:
        for error in errors:
            st.error(error)
        return
    
    # Create the group
    group_email = format_group_email(group_name, domain)
    
    result = run_with_spinner(
        api.create_group,
        f"Creating group {group_email}...",
        group_name,
        trainer_email,
        domain,
        description,
        skip_self
    )
    
    if result:
        StateManager.clear_caches()
        
        # Store success state and rerun to show success message and buttons
        StateManager.set("create_success", True)
        StateManager.set("created_group_email", group_email)
        st.rerun()