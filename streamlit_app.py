"""
Google Group Maker - Streamlit Web Interface

A web frontend for the Google Group Maker CLI tool.
"""

import streamlit as st
import pandas as pd
import time
import traceback
from typing import List, Dict, Any
import io
import csv

from config_utils import load_env, get_env, set_env, save_credentials_file, validate_config, get_config_summary, credentials_exist
from web_utils import GroupMakerAPI

# Page configuration
st.set_page_config(
    page_title="Google Group Maker",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_env()

# Initialize session state
if "debug" not in st.session_state:
    st.session_state.debug = False
if "selected_group" not in st.session_state:
    st.session_state.selected_group = ""
if "groups_cache_timestamp" not in st.session_state:
    st.session_state.groups_cache_timestamp = 0
if "members_cache" not in st.session_state:
    st.session_state.members_cache = {}

# Initialize API
api = GroupMakerAPI(debug=st.session_state.debug)

# Pages configuration
PAGES = [
    "🏠 Dashboard",
    "➕ Create Group",
    "📋 List Groups", 
    "👥 Group Members",
    "👤 Add Members",
    "✏️ Rename Group",
    "🗑️ Delete Group",
    "⚙️ Settings"
]

# Sidebar navigation
with st.sidebar:
    st.title("🔧 Google Group Maker")
    st.markdown("---")
    
    page = st.radio("Navigate to:", PAGES, key="page_selector")
    
    st.markdown("---")
    st.checkbox("Debug mode", key="debug", help="Enable verbose logging")
    
    # Configuration status
    st.markdown("### 🔧 Status")
    config_issues = validate_config()
    if config_issues:
        st.error(f"⚠️ {len(config_issues)} issues")
        with st.expander("View issues"):
            for issue in config_issues:
                st.write(f"• {issue}")
    else:
        st.success("✅ Ready")

# Helper functions
def run_with_spinner(fn, message="Processing...", *args, **kwargs):
    """Execute a function with a spinner and handle errors."""
    with st.spinner(message):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if st.session_state.debug:
                st.code(traceback.format_exc())
            return None

def show_success(message: str):
    """Show success message with toast."""
    st.success(message)
    st.toast(message, icon="✅")

def show_error(message: str):
    """Show error message with toast."""
    st.error(message)
    st.toast(message, icon="❌")

def clear_caches():
    """Clear all cached data."""
    st.session_state.groups_cache_timestamp = 0
    st.session_state.members_cache = {}
    if hasattr(st.session_state, 'groups_data'):
        del st.session_state.groups_data

def format_group_email(group_name: str, domain: str = None) -> str:
    """Format a complete group email address."""
    if "@" in group_name:
        return group_name
    env = get_env()
    domain = domain or env.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com")
    return f"{group_name}@{domain}"

# Page implementations
def page_dashboard():
    """Dashboard page with overview and quick actions."""
    st.title("🏠 Dashboard")
    
    # Configuration summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Configuration Summary")
        config = get_config_summary()
        
        for key, value in config.items():
            if key == "Credentials":
                icon = "✅" if value == "Present" else "❌"
            elif value and value != "Not set":
                icon = "✅"
            else:
                icon = "❌"
            st.write(f"{icon} **{key}**: {value}")
    
    with col2:
        st.subheader("🚀 Quick Actions")
        if st.button("➕ Create Group", use_container_width=True):
            st.session_state.page_selector = "➕ Create Group"
            st.rerun()
        
        if st.button("📋 List Groups", use_container_width=True):
            st.session_state.page_selector = "📋 List Groups"
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.page_selector = "⚙️ Settings"
            st.rerun()
    
    st.markdown("---")
    
    # System status
    st.subheader("🔍 System Status")
    
    if st.button("Test Authentication"):
        result = run_with_spinner(api.ping_auth, "Testing authentication...")
        if result:
            show_success("✅ Authentication successful!")
        else:
            show_error("❌ Authentication failed. Check your configuration.")
    
    # Getting started
    st.markdown("---")
    st.subheader("🚀 Getting Started")
    
    st.info("""
    **First time setup:**
    1. Go to **Settings** to configure your environment variables
    2. Upload your service account credentials file
    3. Test authentication
    4. Create your first group for testing (use a safe name like `test-group-delete-me`)
    
    **Testing commands from CLI:**
    - `./groupmaker.py create test-group-delete-me trainer@example.com`
    - `./groupmaker.py list --query test`
    - `./groupmaker.py delete test-group-delete-me`
    """)

def page_create_group():
    """Create Group page with form inputs."""
    st.title("➕ Create Group")
    
    with st.form("create_group_form"):
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
            domain = st.text_input(
                "Domain",
                value=env.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com"),
                help="Domain for the group email address"
            )
            
            description = st.text_area(
                "Description (optional)",
                placeholder="Brief description of the group",
                max_chars=500
            )
        
        st.subheader("Options")
        
        # Get admin email from environment
        env = get_env()
        admin_email = env.get("ADMIN_EMAIL", env.get("DEFAULT_EMAIL"))
        
        # Show checkbox only if admin email is configured
        if admin_email:
            add_admin = st.checkbox(
                f"Add admin to the group ({admin_email})",
                value=True,  # Checked by default
                help="Add the admin email configured in settings as a group member"
            )
            skip_self = not add_admin  # Invert for the API
        else:
            st.info("ℹ️ No admin email configured. Set ADMIN_EMAIL or DEFAULT_EMAIL in Settings to auto-add yourself to groups.")
            skip_self = True  # Always skip if no admin email
        
        submitted = st.form_submit_button("🚀 Create Group", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if not group_name:
                errors.append("Group name is required")
            else:
                is_valid, error_msg = api.validate_group_name(group_name)
                if not is_valid:
                    errors.append(error_msg)
            
            if not trainer_email or "@" not in trainer_email:
                errors.append("Valid trainer email is required")
            
            if not domain:
                errors.append("Domain is required")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
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
                    show_success(f"🎉 Successfully created group: {group_email}")
                    clear_caches()
                    
                    # Option to view members
                    if st.button("👥 View Group Members"):
                        st.session_state.selected_group = group_email
                        st.session_state.page_selector = "👥 Group Members"
                        st.rerun()

def page_list_groups():
    """List Groups page with search and filtering."""
    st.title("📋 List Groups")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        query = st.text_input("🔍 Search groups", placeholder="Enter search term...")
    
    with col2:
        env = get_env()
        domain = st.text_input("Domain", value=env.get("GOOGLE_GROUP_DOMAIN", ""))
    
    with col3:
        st.write("")  # Spacing
        if st.button("🔄 Refresh", use_container_width=True):
            clear_caches()
    
    # Load and display groups
    cache_key = f"groups_{query}_{domain}_{int(time.time() / 60)}"  # Cache for 1 minute
    
    if cache_key not in st.session_state:
        groups = run_with_spinner(
            api.list_groups,
            "Loading groups...",
            query=query if query else None,
            domain=domain if domain else None
        )
        if groups is not None:
            st.session_state[cache_key] = groups
    else:
        groups = st.session_state[cache_key]
    
    if groups is not None:
        if len(groups) == 0:
            st.info("📭 No groups found matching your criteria.")
        else:
            st.success(f"📊 Found {len(groups)} groups")
            
            # Create DataFrame for display
            df = pd.DataFrame(groups)
            
            # Display table with actions
            for idx, group in enumerate(groups):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{group['email']}**")
                        st.caption(f"Name: {group['name']}")
                        if group['description']:
                            st.caption(f"Description: {group['description']}")
                    
                    with col2:
                        if st.button("👥 Members", key=f"members_{idx}"):
                            st.session_state.selected_group = group['email']
                            st.session_state.page_selector = "👥 Group Members"
                            st.rerun()
                    
                    with col3:
                        if st.button("✏️ Rename", key=f"rename_{idx}"):
                            st.session_state.selected_group = group['email']
                            st.session_state.page_selector = "✏️ Rename Group"
                            st.rerun()
                    
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{idx}"):
                            st.session_state.selected_group = group['email']
                            st.session_state.page_selector = "🗑️ Delete Group"
                            st.rerun()
                    
                    st.divider()

def page_group_members():
    """Group Members page with detailed display."""
    st.title("👥 Group Members")
    
    # Group selection
    if st.session_state.selected_group:
        group_email = st.session_state.selected_group
        st.info(f"Viewing members of: **{group_email}**")
    else:
        group_email = st.text_input("Group Email", placeholder="group-name@domain.com")
    
    if not group_email:
        st.warning("Please select or enter a group email address.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        include_derived = st.checkbox("Include nested group members")
    
    with col2:
        if st.button("🔄 Refresh Members"):
            if group_email in st.session_state.members_cache:
                del st.session_state.members_cache[group_email]
    
    # Load members
    cache_key = f"{group_email}_{include_derived}"
    
    if cache_key not in st.session_state.members_cache:
        members = run_with_spinner(
            api.list_members,
            f"Loading members of {group_email}...",
            group_email,
            include_derived
        )
        if members is not None:
            st.session_state.members_cache[cache_key] = members
    else:
        members = st.session_state.members_cache[cache_key]
    
    if members is not None:
        if len(members) == 0:
            st.info("👤 No members found in this group.")
        else:
            # Summary
            role_counts = {}
            for member in members:
                role = member.get('role', 'UNKNOWN')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            st.success(f"👥 {len(members)} total members")
            
            # Display role summary
            summary_cols = st.columns(len(role_counts))
            for i, (role, count) in enumerate(role_counts.items()):
                emoji = "👑" if role == "OWNER" else "⭐" if role == "MANAGER" else "👤"
                summary_cols[i].metric(f"{emoji} {role}", count)
            
            st.markdown("---")
            
            # Members table
            df = pd.DataFrame(members)
            
            # Display members
            for member in members:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    role_emoji = "👑" if member['role'] == "OWNER" else "⭐" if member['role'] == "MANAGER" else "👤"
                    st.write(f"{role_emoji} **{member['email']}**")
                    if member['name']:
                        st.caption(f"Name: {member['name']}")
                
                with col2:
                    st.write(f"**{member['role']}**")
                
                with col3:
                    st.write(member.get('status', ''))
            
            # Export functionality
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # Email list for copying
                email_list = "\n".join([m['email'] for m in members])
                st.text_area("📧 Email List (copy/paste)", email_list, height=100)
            
            with col2:
                # CSV export
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    "📊 Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{group_email.replace('@', '_')}_members.csv",
                    mime="text/csv"
                )

def page_add_members():
    """Add Members page for batch additions."""
    st.title("👤 Add Members")
    
    with st.form("add_members_form"):
        # Group selection
        if st.session_state.selected_group:
            group_email = st.text_input(
                "Group Email *", 
                value=st.session_state.selected_group,
                disabled=True
            )
        else:
            group_email = st.text_input("Group Email *", placeholder="group-name@domain.com")
        
        # Role selection
        role = st.selectbox(
            "Role *",
            options=["MEMBER", "MANAGER", "OWNER"],
            index=0,
            help="Role to assign to all added members"
        )
        
        # Members input
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
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'email' in df.columns:
                        csv_emails = df['email'].dropna().tolist()
                        st.success(f"📊 Found {len(csv_emails)} emails in CSV")
                        members_text += "\n" + "\n".join(csv_emails)
                    else:
                        st.error("CSV must have an 'email' column")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        # Parse and preview emails
        if members_text:
            parsed_emails = api.parse_email_list(members_text)
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
        
        submitted = st.form_submit_button("👥 Add Members", use_container_width=True)
        
        if submitted:
            if not group_email:
                st.error("Group email is required")
            elif not members_text:
                st.error("Please enter at least one email address")
            else:
                parsed_emails = api.parse_email_list(members_text)
                
                if not parsed_emails:
                    st.error("No valid email addresses found")
                else:
                    # Add members one by one
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
                        time.sleep(0.1)  # Small delay to avoid rate limits
                    
                    # Clear members cache
                    st.session_state.members_cache = {}
                    
                    # Show results
                    if success_count > 0:
                        show_success(f"✅ Successfully added {success_count} members")
                    
                    if error_count > 0:
                        st.error(f"❌ {error_count} members failed to add")
                        with st.expander("View errors"):
                            for error in errors:
                                st.write(f"• {error}")

def page_rename_group():
    """Rename Group page."""
    st.title("✏️ Rename Group")
    
    with st.form("rename_group_form"):
        # Current group
        if st.session_state.selected_group:
            old_group_name = st.text_input(
                "Current Group *", 
                value=st.session_state.selected_group,
                disabled=True
            )
        else:
            old_group_name = st.text_input("Current Group *", placeholder="group-name@domain.com")
        
        # New name
        new_group_name = st.text_input(
            "New Group Name *",
            placeholder="new-group-name",
            help="Enter just the name part (without @domain) or full email address"
        )
        
        if old_group_name and new_group_name:
            # Show preview
            if "@" not in new_group_name and "@" in old_group_name:
                domain = old_group_name.split("@")[1]
                preview = f"{new_group_name}@{domain}"
            else:
                preview = new_group_name
            
            st.info(f"**Preview:** {old_group_name} → {preview}")
        
        st.warning("⚠️ **Warning**: Renaming a group changes its email address. Update any references accordingly.")
        
        submitted = st.form_submit_button("✏️ Rename Group", use_container_width=True)
        
        if submitted:
            if not old_group_name:
                st.error("Current group name is required")
            elif not new_group_name:
                st.error("New group name is required")
            else:
                is_valid, error_msg = api.validate_group_name(new_group_name)
                if not is_valid:
                    st.error(error_msg)
                else:
                    result = run_with_spinner(
                        api.rename_group,
                        f"Renaming group {old_group_name}...",
                        old_group_name,
                        new_group_name
                    )
                    
                    if result:
                        show_success(f"✅ Successfully renamed group to: {new_group_name}")
                        clear_caches()
                        st.session_state.selected_group = ""

def page_delete_group():
    """Delete Group page with confirmation."""
    st.title("🗑️ Delete Group")
    
    st.warning("⚠️ **DANGER ZONE** - This action cannot be undone!")
    
    with st.form("delete_group_form"):
        # Group selection
        if st.session_state.selected_group:
            group_email = st.text_input(
                "Group to Delete *", 
                value=st.session_state.selected_group,
                disabled=True
            )
        else:
            group_email = st.text_input("Group to Delete *", placeholder="group-name@domain.com")
        
        st.error(f"""
        **You are about to permanently delete: {group_email or '[GROUP_EMAIL]'}**
        
        This will:
        • Remove all members from the group
        • Delete all group content and history
        • Make the group email address unusable
        • Cannot be undone
        """)
        
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
        
        # Enable delete button only with double confirmation
        delete_enabled = (
            confirm1 and 
            confirm2 == group_email and 
            group_email
        )
        
        submitted = st.form_submit_button(
            "🗑️ PERMANENTLY DELETE GROUP",
            use_container_width=True,
            type="primary",
            disabled=not delete_enabled
        )
        
        if submitted:
            if delete_enabled:
                result = run_with_spinner(
                    api.delete_group,
                    f"Deleting group {group_email}...",
                    group_email
                )
                
                if result:
                    show_success(f"🗑️ Successfully deleted group: {group_email}")
                    clear_caches()
                    st.session_state.selected_group = ""
                    
                    # Navigate back to list
                    if st.button("📋 Back to Group List"):
                        st.session_state.page_selector = "📋 List Groups"
                        st.rerun()
            else:
                st.error("Please complete all confirmation steps")

def page_settings():
    """Settings page for configuration."""
    st.title("⚙️ Settings")
    
    # Environment variables
    st.subheader("🔧 Environment Configuration")
    
    current_env = get_env()
    
    with st.form("env_settings_form"):
        default_email = st.text_input(
            "DEFAULT_EMAIL *",
            value=current_env.get("DEFAULT_EMAIL", ""),
            help="Your email address (required)"
        )
        
        google_group_domain = st.text_input(
            "GOOGLE_GROUP_DOMAIN",
            value=current_env.get("GOOGLE_GROUP_DOMAIN", ""),
            placeholder="tinkertanker.com",
            help="Default domain for groups (optional)"
        )
        
        admin_email = st.text_input(
            "ADMIN_EMAIL",
            value=current_env.get("ADMIN_EMAIL", ""),
            placeholder="Uses DEFAULT_EMAIL if not set",
            help="Admin email for authentication (optional)"
        )
        
        if st.form_submit_button("💾 Save Environment Settings"):
            new_env = {
                "DEFAULT_EMAIL": default_email,
                "GOOGLE_GROUP_DOMAIN": google_group_domain,
                "ADMIN_EMAIL": admin_email
            }
            
            try:
                set_env(new_env)
                show_success("✅ Environment settings saved successfully!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to save settings: {e}")
    
    st.markdown("---")
    
    # Service account credentials
    st.subheader("🔐 Service Account Credentials")
    
    if credentials_exist():
        st.success("✅ Credentials file found: `service-account-credentials.json`")
    else:
        st.error("❌ Credentials file not found")
    
    uploaded_file = st.file_uploader(
        "Upload new service account credentials",
        type=['json'],
        help="Upload your service-account-credentials.json file"
    )
    
    if uploaded_file:
        try:
            # Validate it's JSON
            import json
            json.loads(uploaded_file.getvalue().decode())
            
            if st.button("💾 Save Credentials File"):
                save_credentials_file(uploaded_file.getvalue())
                show_success("✅ Credentials file saved successfully!")
                st.rerun()
                
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file. Please upload a valid service account credentials file.")
    
    st.warning("""
    **Security Note**: The credentials file is saved locally and should never be committed to version control.
    Make sure your `.gitignore` includes `service-account-credentials.json`.
    """)
    
    st.markdown("---")
    
    # Authentication test
    st.subheader("🧪 Test Authentication")
    
    if st.button("🔍 Test Connection"):
        if not credentials_exist():
            show_error("❌ No credentials file found. Please upload credentials first.")
        elif not current_env.get("DEFAULT_EMAIL"):
            show_error("❌ DEFAULT_EMAIL not set. Please configure environment variables first.")
        else:
            result = run_with_spinner(api.ping_auth, "Testing authentication...")
            if result:
                show_success("✅ Authentication successful! You can now use all features.")
            else:
                show_error("❌ Authentication failed. Check your credentials and configuration.")

# Main app routing
page_map = {
    "🏠 Dashboard": page_dashboard,
    "➕ Create Group": page_create_group,
    "📋 List Groups": page_list_groups,
    "👥 Group Members": page_group_members,
    "👤 Add Members": page_add_members,
    "✏️ Rename Group": page_rename_group,
    "🗑️ Delete Group": page_delete_group,
    "⚙️ Settings": page_settings
}

# Render the selected page
if page in page_map:
    page_map[page]()
else:
    st.error(f"Page '{page}' not found")

# Footer
st.markdown("---")
st.markdown(
    "💡 **Tip**: Start with the Settings page to configure your environment, "
    "then test with a safe group name like `test-group-delete-me`"
)
