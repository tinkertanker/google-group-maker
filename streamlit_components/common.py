"""
Compatibility layer for streamlit_components.

This module re-exports all components from their focused submodules for backward
compatibility. Existing code can continue to import from this module while new
code can import directly from the specific component modules.

Component modules:
- feedback_components: User feedback messages (success, error, warning, info)
- input_components: Input widgets (selectors, text inputs, confirmations)
- display_components: Display widgets (member display, exports, action buttons)
- execution_helpers: Execution utilities (spinners, formatters)

For new code, prefer importing directly from the specific modules, e.g.:
    from streamlit_components.feedback_components import show_success
    from streamlit_components.input_components import group_selector
"""

from .feedback_components import show_success, show_error, show_warning, show_info
from .input_components import (
    group_selector, role_selector, email_input,
    domain_input, confirmation_dialog
)
from .display_components import member_display, export_members_section, action_buttons
from .execution_helpers import run_with_spinner, format_group_email

# Explicit re-exports for clarity
__all__ = [
    # Feedback components
    'show_success',
    'show_error',
    'show_warning',
    'show_info',
    # Input components
    'group_selector',
    'role_selector',
    'email_input',
    'domain_input',
    'confirmation_dialog',
    # Display components
    'member_display',
    'export_members_section',
    'action_buttons',
    # Execution helpers
    'run_with_spinner',
    'format_group_email'
]