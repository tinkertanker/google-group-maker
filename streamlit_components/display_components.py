"""
Display components for Google Group Maker Streamlit app.

Provides components for displaying members, exporting data, and group action buttons.
"""

import io
from typing import List, Tuple, Dict, Any

import pandas as pd
import streamlit as st

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import ROLE_EMOJIS
from .feedback_components import show_info

__all__ = [
    'member_display',
    'export_members_section',
    'action_buttons'
]


def member_display(members: List[Dict[str, Any]]) -> None:
    """Display members in a formatted way with role summaries and detailed listings.

    Args:
        members: List of member dictionaries following the API schema.
                 Each dictionary must contain the following keys:
                 
                 - 'email' (str): Member's email address (required, primary identifier)
                 - 'name' (str): Display name of the member (optional, may be empty)
                 - 'role' (str): Member's role in the group (OWNER, MANAGER, or MEMBER)
                 - 'type' (str): Member type (e.g., USER, GROUP, SERVICE_ACCOUNT)
                 - 'status' (str): Membership status (e.g., ACTIVE, SUSPENDED)
                 
                 Example member dict:
                 {
                     'email': 'user@example.com',
                     'name': 'John Doe',
                     'role': 'MEMBER',
                     'type': 'USER',
                     'status': 'ACTIVE'
                 }
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


def export_members_section(members: List[Dict[str, Any]], group_email: str) -> None:
    """Section for exporting member data.

    Args:
        members: List of member dictionaries following the API schema
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


def action_buttons(group: Dict[str, Any], index: int) -> Tuple[bool, str]:
    """Display action buttons for a group.

    Args:
        group: Group dictionary following the API schema (email, name, description)
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