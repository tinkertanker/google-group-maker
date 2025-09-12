"""
Google Group Maker - Streamlit Web Interface (Refactored)

A modular web frontend for the Google Group Maker CLI tool.
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_utils import load_env, validate_config
from web_utils import GroupMakerAPI
from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import (
    APP_TITLE, APP_ICON, LAYOUT, PAGES
)

# Import page modules
from streamlit_pages.dashboard import render_dashboard
from streamlit_pages.create_group import render_create_group
from streamlit_pages.list_groups import render_list_groups
from streamlit_pages.group_members import render_group_members
from streamlit_pages.add_members import render_add_members
from streamlit_pages.rename_group import render_rename_group
from streamlit_pages.delete_group import render_delete_group
from streamlit_pages.settings import render_settings


def initialize_app() -> None:
    """Initialize the Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded"
    )
    
    # Load environment variables
    load_env()
    
    # Initialize state manager
    StateManager.initialize()


def render_sidebar() -> str:
    """Render the sidebar navigation.
    
    Returns:
        Selected page name
    """
    with st.sidebar:
        st.title(f"🔧 {APP_TITLE}")
        st.markdown("---")
        
        # Check if navigation was requested
        next_page = StateManager.get("next_page")
        if next_page:
            # Clear the navigation request
            StateManager.set("next_page", None)
            default_page = next_page
        else:
            default_page = StateManager.get("current_page", PAGES[0])
        
        # Ensure default_page is in PAGES
        if default_page not in PAGES:
            default_page = PAGES[0]
        
        # Page selector
        page = st.radio(
            "Navigate to:", 
            PAGES, 
            key="page_selector",
            index=PAGES.index(default_page)
        )
        
        # Store current page
        StateManager.set("current_page", page)
        
        st.markdown("---")
        
        # Debug mode toggle
        debug_mode = st.checkbox(
            "Debug mode", 
            value=StateManager.get_debug(),
            help="Enable verbose logging"
        )
        StateManager.set_debug(debug_mode)
        
        # Configuration status
        render_config_status()
        
        return page


def render_config_status() -> None:
    """Render configuration status in sidebar."""
    st.markdown("### 🔧 Status")
    
    config_issues = validate_config()
    
    if config_issues:
        st.error(f"⚠️ {len(config_issues)} issues")
        with st.expander("View issues"):
            for issue in config_issues:
                st.write(f"• {issue}")
    else:
        st.success("✅ Ready")


def render_footer() -> None:
    """Render the footer."""
    st.markdown("---")
    st.markdown(
        "💡 **Tip**: Start with the Settings page to configure your environment, "
        "then test with a safe group name like `test-group-delete-me`"
    )


def main() -> None:
    """Main application entry point."""
    # Initialize app
    initialize_app()
    
    # Initialize API with debug mode
    api = GroupMakerAPI(debug=StateManager.get_debug())
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Page routing map
    page_map = {
        "🏠 Dashboard": render_dashboard,
        "➕ Create Group": render_create_group,
        "📋 List Groups": render_list_groups,
        "👥 Group Members": render_group_members,
        "👤 Add Members": render_add_members,
        "✏️ Rename Group": render_rename_group,
        "🗑️ Delete Group": render_delete_group,
        "⚙️ Settings": render_settings
    }
    
    # Render the selected page
    if selected_page in page_map:
        page_function = page_map[selected_page]
        try:
            page_function(api)
        except Exception as e:
            st.error(f"Error rendering page: {str(e)}")
            if StateManager.get_debug():
                import traceback
                st.code(traceback.format_exc())
    else:
        st.error(f"Page '{selected_page}' not found")
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()