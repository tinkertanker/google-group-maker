"""
Feedback and messaging components for Google Group Maker Streamlit app.

Provides consistent user feedback through success, error, warning, and info messages
with toast notifications.
"""

import streamlit as st

__all__ = [
    'show_success',
    'show_error',
    'show_warning',
    'show_info'
]


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