"""
Execution helper utilities for Google Group Maker Streamlit app.

Provides utilities for executing functions with spinners, error handling,
and formatting helpers.

Note: run_with_spinner surfaces full tracebacks only when debug mode is enabled
in StateManager, ensuring production users see clean error messages while
developers get detailed diagnostic information.
"""

import traceback
from typing import Any, Callable, Optional

import streamlit as st

from streamlit_utils.state_manager import StateManager
from streamlit_utils.config import DEFAULT_DOMAIN

__all__ = [
    'run_with_spinner',
    'format_group_email'
]


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