"""
Input components for Google Group Maker Streamlit app.

Provides reusable input widgets for groups, roles, emails, domains, and confirmations.
"""

from typing import Optional

import streamlit as st

from streamlit_utils.state_manager import StateManager

__all__ = [
    'group_selector',
    'role_selector',
    'email_input',
    'domain_input',
    'confirmation_dialog'
]


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