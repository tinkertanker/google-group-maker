"""
Create Group page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Optional, List

from config_utils import get_env
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, ERROR_MESSAGES
from streamlit_components.common import (
    run_with_spinner, show_success, show_error, show_info,
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
        partial_success = StateManager.get("partial_success", False)
        
        if partial_success:
            show_success(f"✅ Group created: {group_created}")
            st.warning("⚠️ Some trainers could not be added. You can retry from the 'Add Members' page.")
        else:
            show_success(SUCCESS_MESSAGES["group_created"].format(group_email=group_created))
        
        # Clear the success flag
        StateManager.set("create_success", False)
        StateManager.set("created_group_email", None)
        StateManager.set("partial_success", False)
        
        # Show navigation buttons (outside form!)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👥 View Group Members", use_container_width=True):
                StateManager.set_selected_group(group_created)
                StateManager.navigate_to("👥 Group Members")
        with col2:
            if partial_success and st.button("👤 Add Failed Members", use_container_width=True):
                StateManager.set_selected_group(group_created)
                StateManager.navigate_to("👤 Add Members")
        with col3:
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
            
            # New: Support multiple trainer emails
            st.markdown("**Trainer Emails** *")
            num_trainers = st.number_input(
                "Number of trainers to add",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                help="How many trainer emails would you like to add?"
            )
            
            trainer_emails = []
            for i in range(int(num_trainers)):
                email = st.text_input(
                    f"Trainer {i+1} Email",
                    placeholder="trainer@example.com",
                    key=f"trainer_email_{i}",
                    help="Email of the external trainer to add to the group"
                )
                if email:
                    trainer_emails.append(email)
        
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
            
            # Show preview of trainers to be added
            if trainer_emails:
                st.markdown("**Trainers to be added:**")
                for email in trainer_emails:
                    st.write(f"• {email}")
        
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
                api, group_name, trainer_emails, 
                domain, description, skip_self
            )


def _handle_create_group(api: GroupMakerAPI, 
                        group_name: str,
                        trainer_emails: List[str],
                        domain: str,
                        description: str,
                        skip_self: bool) -> None:
    """Handle group creation.
    
    Args:
        api: GroupMakerAPI instance
        group_name: Name of the group
        trainer_emails: List of trainer emails
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
    
    if not trainer_emails:
        errors.append("At least one trainer email is required")
    else:
        # Validate all trainer emails
        for email in trainer_emails:
            if not email or "@" not in email:
                errors.append(f"Invalid email address: {email}")
    
    if not domain:
        errors.append(ERROR_MESSAGES["domain_required"])
    
    if errors:
        for error in errors:
            st.error(error)
        return
    
    # Create the group with the first trainer
    group_email = format_group_email(group_name, domain)
    
    # Create group with first trainer
    result = run_with_spinner(
        api.create_group,
        f"Creating group {group_email}...",
        group_name,
        trainer_emails[0],  # Use first trainer for creation
        domain,
        description,
        skip_self
    )
    
    if result:
        # Track overall success
        group_created_successfully = True
        all_trainers_added = True
        
        # Add remaining trainers if any
        if len(trainer_emails) > 1:
            show_info(f"Adding {len(trainer_emails) - 1} additional trainers...")
            
            success_count = 0
            failed_emails = []
            added_emails = []  # Track successfully added emails for potential rollback
            
            for trainer_email in trainer_emails[1:]:
                try:
                    # Add each additional trainer as a member
                    api.add_member(group_email, trainer_email, "MEMBER")
                    success_count += 1
                    added_emails.append(trainer_email)
                except Exception as e:
                    failed_emails.append(f"{trainer_email}: {str(e)}")
                    all_trainers_added = False
            
            if success_count > 0:
                show_success(f"Added {success_count} additional trainers successfully")
            
            if failed_emails:
                st.warning("⚠️ Some trainers could not be added:")
                for error in failed_emails:
                    st.write(f"• {error}")
                
                # Store failed emails in session state for retry
                StateManager.set("failed_trainer_emails", [email.split(":")[0].strip() for email in failed_emails])
                StateManager.set("retry_group_email", group_email)
                
                # Offer retry option
                st.info("💡 You can retry adding the failed trainers from the 'Add Members' page")
        
        StateManager.clear_caches()
        
        # Store success state and rerun to show success message and buttons
        StateManager.set("create_success", True)
        StateManager.set("created_group_email", group_email)
        StateManager.set("partial_success", not all_trainers_added)
        st.rerun()
    else:
        # Group creation failed - no rollback needed as nothing was created
        show_error("Failed to create group. Please check your settings and try again.")