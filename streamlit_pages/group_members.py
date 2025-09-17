"""
Group Members page for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import List, Dict

from streamlit_utils.state_manager import StateManager
from streamlit_utils.cache import cached_list_members, clear_member_cache
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
        _display_members(members, group_email, api)
    else:
        st.error("Failed to load members. Please check the group email and try again.")


def _display_members(members: List[Dict[str, str]], group_email: str, api: GroupMakerAPI) -> None:
    """Display group members.

    Args:
        members: List of member dictionaries
        group_email: Email of the group
        api: GroupMakerAPI instance
    """
    if len(members) == 0:
        st.info("👤 No members found in this group.")

        # Offer to add members
        if st.button("➕ Add First Member", use_container_width=True):
            StateManager.set_selected_group(group_email)
            StateManager.navigate_to("👤 Add Members")
        return

    # Add member removal section
    st.markdown("### 🗑️ Remove Members")

    # Create checkboxes for each member
    selected_members = []

    with st.expander("Select members to remove", expanded=False):
        # Add warning about removal
        st.info("💡 Select one or more members below to remove them from the group")
        select_all = st.checkbox("Select all members", key="select_all_members")

        st.markdown("---")

        for i, member in enumerate(members):
            member_email = member.get('email', '')
            member_role = member.get('role', 'MEMBER')

            # Create unique key for each checkbox
            checkbox_key = f"member_checkbox_{i}_{member_email}"

            # Display checkbox with member info
            col1, col2 = st.columns([3, 1])
            with col1:
                is_selected = st.checkbox(
                    f"{member_email}",
                    value=select_all,
                    key=checkbox_key
                )
            with col2:
                st.caption(member_role)

            if is_selected:
                selected_members.append(member_email)

        if selected_members:
            st.warning(f"⚠️ {len(selected_members)} member(s) selected for removal")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Remove Selected Members", type="primary", use_container_width=True):
                    _remove_members(api, group_email, selected_members)
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.rerun()

    st.markdown("---")

    # Display members with summary
    member_display(members)

    # Export section
    export_members_section(members, group_email)


def _remove_members(api: GroupMakerAPI, group_email: str, member_emails: List[str]) -> None:
    """Remove selected members from the group.

    Args:
        api: GroupMakerAPI instance
        group_email: Email of the group
        member_emails: List of member emails to remove
    """

    with st.spinner(f"Removing {len(member_emails)} member(s)..."):
        try:
            if len(member_emails) == 1:
                # Single member removal
                result = api.remove_member(group_email, member_emails[0])
                if result.get("success"):
                    show_success(f"✅ Successfully removed {member_emails[0]}")
                else:
                    show_error(f"Failed to remove {member_emails[0]}: {result.get('message')}")
            else:
                # Batch removal
                result = api.remove_members_batch(group_email, member_emails)

                summary = result.get("summary", {})
                successful = summary.get("successful", 0)
                failed = summary.get("failed", 0)

                if result.get("success"):
                    show_success(f"✅ Successfully removed all {successful} members")
                elif result.get("partial_success"):
                    show_warning(f"⚠️ Removed {successful} members, failed to remove {failed} members")

                    # Show details of failures
                    if summary.get("failed_emails"):
                        st.error("Failed to remove:")
                        for email in summary.get("failed_emails", []):
                            st.write(f"- {email}")
                else:
                    show_error(f"Failed to remove all members. {failed} member(s) could not be removed")

            # Clear cache and refresh
            clear_member_cache(group_email)
            StateManager.clear_members_cache(group_email)
            st.rerun()

        except Exception as e:
            show_error(f"Error removing members: {str(e)}")