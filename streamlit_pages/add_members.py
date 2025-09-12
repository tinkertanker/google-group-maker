"""
Add Members page for Google Group Maker Streamlit app.
"""

import streamlit as st
import pandas as pd
import time
from typing import List, Optional

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import SUCCESS_MESSAGES, MEMBER_BATCH_DELAY
from streamlit_utils.cache import clear_member_cache
from streamlit_components.common import (
    group_selector, role_selector, show_success, show_error
)
from web_utils import GroupMakerAPI


def render_add_members(api: GroupMakerAPI) -> None:
    """Render the add members page.
    
    Args:
        api: GroupMakerAPI instance
    """
    st.title("👤 Add Members")
    
    with st.form("add_members_form"):
        # Group selection
        group_email = group_selector(
            key="add_members_group",
            label="Group Email",
            required=True
        )
        
        # Role selection
        role = role_selector(key="add_members_role")
        
        # Members input section
        st.subheader("Members to Add")
        
        col1, col2 = st.columns(2)
        
        with col1:
            members_text = st.text_area(
                "Email Addresses *",
                placeholder="Enter email addresses (one per line or comma-separated)",
                height=200,
                help="Supported formats: one per line, comma-separated, or semicolon-separated"
            )
        
        with col2:
            uploaded_file = st.file_uploader(
                "Or upload CSV file",
                type=['csv'],
                help="CSV file with 'email' column"
            )
            
            if uploaded_file:
                csv_emails = _process_csv_upload(uploaded_file)
                if csv_emails:
                    members_text = _append_csv_emails(members_text, csv_emails)
        
        # Parse and preview emails
        if members_text:
            parsed_emails = api.parse_email_list(members_text)
            _preview_emails(parsed_emails)
        
        submitted = st.form_submit_button("👥 Add Members", use_container_width=True)
        
        if submitted:
            _handle_add_members(api, group_email, members_text, role)


def _process_csv_upload(uploaded_file) -> Optional[List[str]]:
    """Process uploaded CSV file.
    
    Args:
        uploaded_file: Uploaded CSV file
        
    Returns:
        List of emails or None if error
    """
    try:
        df = pd.read_csv(uploaded_file)
        if 'email' in df.columns:
            csv_emails = df['email'].dropna().tolist()
            st.success(f"📊 Found {len(csv_emails)} emails in CSV")
            return csv_emails
        else:
            st.error("CSV must have an 'email' column")
            return None
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return None


def _append_csv_emails(existing_text: str, csv_emails: List[str]) -> str:
    """Append CSV emails to existing text.
    
    Args:
        existing_text: Existing email text
        csv_emails: Emails from CSV
        
    Returns:
        Combined email text
    """
    if existing_text:
        return existing_text + "\n" + "\n".join(csv_emails)
    return "\n".join(csv_emails)


def _preview_emails(parsed_emails: List[str]) -> None:
    """Preview parsed email addresses.
    
    Args:
        parsed_emails: List of parsed emails
    """
    st.info(f"📧 Found {len(parsed_emails)} valid email addresses")
    
    if len(parsed_emails) > 10:
        with st.expander("Preview first 10 emails"):
            for email in parsed_emails[:10]:
                st.write(f"• {email}")
            st.write(f"... and {len(parsed_emails) - 10} more")
    elif parsed_emails:
        st.write("**Preview:**")
        for email in parsed_emails:
            st.write(f"• {email}")


def _handle_add_members(api: GroupMakerAPI,
                       group_email: str,
                       members_text: str,
                       role: str) -> None:
    """Handle adding members to group.
    
    Args:
        api: GroupMakerAPI instance
        group_email: Group email
        members_text: Text containing emails
        role: Role to assign
    """
    # Validation
    if not group_email:
        show_error("Group email is required")
        return
    
    if not members_text:
        show_error("Please enter at least one email address")
        return
    
    parsed_emails = api.parse_email_list(members_text)
    
    if not parsed_emails:
        show_error("No valid email addresses found")
        return
    
    # Add members with progress tracking
    progress_bar = st.progress(0)
    success_count = 0
    error_count = 0
    errors = []
    
    for i, email in enumerate(parsed_emails):
        try:
            api.add_member(group_email, email, role)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"{email}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(parsed_emails))
        time.sleep(MEMBER_BATCH_DELAY)  # Small delay to avoid rate limits
    
    # Clear caches
    clear_member_cache(group_email)
    StateManager.clear_members_cache(group_email)
    
    # Show results
    if success_count > 0:
        show_success(SUCCESS_MESSAGES["members_added"].format(count=success_count))
    
    if error_count > 0:
        st.error(f"❌ {error_count} members failed to add")
        with st.expander("View errors"):
            for error in errors:
                st.write(f"• {error}")