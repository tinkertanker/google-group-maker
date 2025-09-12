"""
Centralized state management for Google Group Maker Streamlit app.
"""

import streamlit as st
from typing import Any, Optional, Dict, List
import time

class StateManager:
    """Manages application state in a centralized manner."""
    
    # State keys
    DEBUG = "debug"
    SELECTED_GROUP = "selected_group"
    GROUPS_CACHE_TIMESTAMP = "groups_cache_timestamp"
    MEMBERS_CACHE = "members_cache"
    PAGE_SELECTOR = "page_selector"
    GROUPS_DATA = "groups_data"
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize all required session state variables."""
        defaults = {
            cls.DEBUG: False,
            cls.SELECTED_GROUP: "",
            cls.GROUPS_CACHE_TIMESTAMP: 0,
            cls.MEMBERS_CACHE: {},
            cls.GROUPS_DATA: None
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from session state.
        
        Args:
            key: The state key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default
        """
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a value in session state.
        
        Args:
            key: The state key to set
            value: The value to set
        """
        st.session_state[key] = value
    
    @classmethod
    def delete(cls, key: str) -> None:
        """Delete a key from session state if it exists.
        
        Args:
            key: The state key to delete
        """
        if key in st.session_state:
            del st.session_state[key]
    
    @classmethod
    def clear_caches(cls) -> None:
        """Clear all cached data."""
        cls.set(cls.GROUPS_CACHE_TIMESTAMP, 0)
        cls.set(cls.MEMBERS_CACHE, {})
        cls.delete(cls.GROUPS_DATA)
    
    @classmethod
    def get_debug(cls) -> bool:
        """Get debug mode status."""
        return cls.get(cls.DEBUG, False)
    
    @classmethod
    def set_debug(cls, value: bool) -> None:
        """Set debug mode status."""
        cls.set(cls.DEBUG, value)
    
    @classmethod
    def get_selected_group(cls) -> str:
        """Get currently selected group."""
        return cls.get(cls.SELECTED_GROUP, "")
    
    @classmethod
    def set_selected_group(cls, group_email: str) -> None:
        """Set currently selected group."""
        cls.set(cls.SELECTED_GROUP, group_email)
    
    @classmethod
    def clear_selected_group(cls) -> None:
        """Clear the selected group."""
        cls.set(cls.SELECTED_GROUP, "")
    
    @classmethod
    def cache_members(cls, group_email: str, include_derived: bool, members: List[Dict]) -> None:
        """Cache member list for a group.
        
        Args:
            group_email: The group email
            include_derived: Whether derived members are included
            members: List of member dictionaries
        """
        cache = cls.get(cls.MEMBERS_CACHE, {})
        cache_key = f"{group_email}_{include_derived}"
        cache[cache_key] = members
        cls.set(cls.MEMBERS_CACHE, cache)
    
    @classmethod
    def get_cached_members(cls, group_email: str, include_derived: bool) -> Optional[List[Dict]]:
        """Get cached members for a group.
        
        Args:
            group_email: The group email
            include_derived: Whether derived members are included
            
        Returns:
            Cached members list or None if not cached
        """
        cache = cls.get(cls.MEMBERS_CACHE, {})
        cache_key = f"{group_email}_{include_derived}"
        return cache.get(cache_key)
    
    @classmethod
    def clear_members_cache(cls, group_email: Optional[str] = None) -> None:
        """Clear members cache for a specific group or all groups.
        
        Args:
            group_email: Optional group email to clear cache for
        """
        if group_email:
            cache = cls.get(cls.MEMBERS_CACHE, {})
            keys_to_delete = [k for k in cache.keys() if k.startswith(f"{group_email}_")]
            for key in keys_to_delete:
                del cache[key]
            cls.set(cls.MEMBERS_CACHE, cache)
        else:
            cls.set(cls.MEMBERS_CACHE, {})
    
    @classmethod
    def navigate_to(cls, page: str) -> None:
        """Navigate to a specific page.
        
        Args:
            page: The page name to navigate to
        """
        # Use a different key for navigation to avoid conflict with radio widget
        cls.set("next_page", page)
        st.rerun()