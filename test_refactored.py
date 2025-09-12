#!/usr/bin/env python3
"""
Quick test script to verify the refactored app works.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work correctly."""
    print("Testing imports...")
    
    try:
        # Test utility imports
        from streamlit_utils.state_manager import StateManager
        from streamlit_utils.config import APP_TITLE
        from streamlit_utils.cache import cached_list_groups
        from streamlit_utils.error_handler import with_retry
        print("✓ Utility imports OK")
        
        # Test component imports
        from streamlit_components.common import show_success
        print("✓ Component imports OK")
        
        # Test page imports
        from streamlit_pages.dashboard import render_dashboard
        from streamlit_pages.create_group import render_create_group
        from streamlit_pages.list_groups import render_list_groups
        print("✓ Page imports OK")
        
        # Test API
        from web_utils import GroupMakerAPI
        api = GroupMakerAPI(debug=False)
        print("✓ API initialization OK")
        
        print("\n✅ All imports successful! The refactored app should work.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)