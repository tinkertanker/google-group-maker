"""
Reusable UI components for Google Group Maker Streamlit app.
"""

import streamlit as st
import traceback
from typing import Any, Callable, Optional, List, Tuple
import pandas as pd
import io

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import ROLE_EMOJIS, DEFAULT_DOMAIN


def run_with_spinner(fn: Callable, message: str = "Processing...", *args, **kwargs) -> Optional[Any]:
    """Execute a function with a spinner and handle errors.
    
    Args:
        fn: Function to execute
        message: Spinner message
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if error occurred
    """
    with st.spinner(message):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if StateManager.get_debug():
                st.code(traceback.format_exc())
            return None


def show_success(message: str) -> None:
    """Show success message with toast.
    
    Args:
        message: Success message to display
    """
    st.success(message)
    st.toast(message, icon="✅")


def show_error(message: str) -> None:
    """Show error message with toast.
    
    Args:
        message: Error message to display
    """
    st.error(message)
    st.toast(message, icon="❌")


def show_warning(message: str) -> None:
    """Show warning message.
    
    Args:
        message: Warning message to display
    """
    st.warning(message)


def show_info(message: str) -> None:
    """Show info message.
    
    Args:
        message: Info message to display
    """
    st.info(message)


def group_selector(key: str = "group_selector", 
                  label: str = "Group Email", 
                  disabled: bool = False,
                  required: bool = True) -> str:
    """Reusable group selector component.
    
    Args:
        key: Unique key for the component
        label: Label for the input field
        disabled: Whether to disable the input
        required: Whether the field is required
        
    Returns:
        Selected group email
    """
    selected_group = StateManager.get_selected_group()
    
    if selected_group:
        return st.text_input(
            f"{label} {'*' if required else ''}",
            value=selected_group,
            disabled=True,
            key=key
        )
    else:
        return st.text_input(
            f"{label} {'*' if required else ''}",
            placeholder="group-name@domain.com",
            disabled=disabled,
            key=key
        )


def role_selector(key: str = "role_selector", 
                 default_index: int = 0) -> str:
    """Reusable role selector component.
    
    Args:
        key: Unique key for the component
        default_index: Default selected index
        
    Returns:
        Selected role
    """
    return st.selectbox(
        "Role *",
        options=["MEMBER", "MANAGER", "OWNER"],
        index=default_index,
        help="Role to assign to the member(s)",
        key=key
    )


def email_input(key: str = "email_input",
               label: str = "Email Address",
               placeholder: str = "user@example.com",
               required: bool = True,
               help_text: Optional[str] = None) -> str:
    """Reusable email input component.
    
    Args:
        key: Unique key for the component
        label: Label for the input field
        placeholder: Placeholder text
        required: Whether the field is required
        help_text: Optional help text
        
    Returns:
        Entered email address
    """
    return st.text_input(
        f"{label} {'*' if required else ''}",
        placeholder=placeholder,
        help=help_text,
        key=key
    )


def domain_input(key: str = "domain_input",
                default_value: str = "",
                required: bool = False) -> str:
    """Reusable domain input component.
    
    Args:
        key: Unique key for the component
        default_value: Default domain value
        required: Whether the field is required
        
    Returns:
        Entered domain
    """
    return st.text_input(
        f"Domain {'*' if required else ''}",
        value=default_value,
        help="Domain for the group email address",
        key=key
    )


def confirmation_dialog(message: str, 
                       confirm_text: str = "Confirm",
                       key_prefix: str = "confirm") -> bool:
    """Show a confirmation dialog.
    
    Args:
        message: Confirmation message
        confirm_text: Text for confirmation button
        key_prefix: Prefix for component keys
        
    Returns:
        True if confirmed, False otherwise
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(confirm_text, key=f"{key_prefix}_yes", type="primary"):
            return True
    
    with col2:
        if st.button("Cancel", key=f"{key_prefix}_no"):
            return False
    
    return False


def member_display(members: List[dict]) -> None:
    """Display members in a formatted way.
    
    Args:
        members: List of member dictionaries
    """
    if not members:
        show_info("👤 No members found in this group.")
        return
    
    # Summary
    role_counts = {}
    for member in members:
        role = member.get('role', 'UNKNOWN')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    st.success(f"👥 {len(members)} total members")
    
    # Display role summary
    summary_cols = st.columns(len(role_counts))
    for i, (role, count) in enumerate(role_counts.items()):
        emoji = ROLE_EMOJIS.get(role, "👤")
        summary_cols[i].metric(f"{emoji} {role}", count)
    
    st.markdown("---")
    
    # Display members
    for member in members:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            role_emoji = ROLE_EMOJIS.get(member['role'], "👤")
            st.write(f"{role_emoji} **{member['email']}**")
            if member.get('name'):
                st.caption(f"Name: {member['name']}")
        
        with col2:
            st.write(f"**{member['role']}**")
        
        with col3:
            st.write(member.get('status', ''))


def export_members_section(members: List[dict], group_email: str) -> None:
    """Section for exporting member data.
    
    Args:
        members: List of member dictionaries
        group_email: Email of the group
    """
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Email list for copying
        email_list = "\n".join([m['email'] for m in members])
        st.text_area("📧 Email List (copy/paste)", email_list, height=100)
    
    with col2:
        # CSV export
        df = pd.DataFrame(members)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        st.download_button(
            "📊 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{group_email.replace('@', '_')}_members.csv",
            mime="text/csv"
        )


def format_group_email(group_name: str, domain: Optional[str] = None) -> str:
    """Format a complete group email address.
    
    Args:
        group_name: Name of the group
        domain: Optional domain
        
    Returns:
        Formatted email address
    """
    if "@" in group_name:
        return group_name
    
    # Use domain if provided, otherwise use default
    domain = domain or DEFAULT_DOMAIN
    return f"{group_name}@{domain}"


def action_buttons(group: dict, index: int) -> Tuple[bool, str]:
    """Display action buttons for a group.
    
    Args:
        group: Group dictionary
        index: Index for unique keys
        
    Returns:
        Tuple of (action_clicked, action_type)
    """
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.write(f"**{group['email']}**")
        st.caption(f"Name: {group['name']}")
        if group.get('description'):
            st.caption(f"Description: {group['description']}")
    
    action_clicked = False
    action_type = ""
    
    with col2:
        if st.button("👥 Members", key=f"members_{index}"):
            StateManager.set_selected_group(group['email'])
            action_clicked = True
            action_type = "members"
    
    with col3:
        if st.button("✏️ Rename", key=f"rename_{index}"):
            StateManager.set_selected_group(group['email'])
            action_clicked = True
            action_type = "rename"
    
    with col4:
        if st.button("🗑️ Delete", key=f"delete_{index}"):
            StateManager.set_selected_group(group['email'])
            action_clicked = True
            action_type = "delete"
    
    st.divider()
    
    return action_clicked, action_type