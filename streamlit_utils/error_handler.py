"""
Error handling utilities with retry logic for Google Group Maker.
"""

import functools
import time
import logging
import streamlit as st
from typing import Any, Callable, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Exception that indicates an operation can be retried."""
    pass


class RateLimitError(RetryableError):
    """Exception for rate limit errors."""
    pass


def with_retry(max_attempts: int = 3, 
               delay: float = 1.0,
               backoff: float = 2.0,
               exceptions: tuple = (RetryableError,)) -> Callable:
    """Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        return cast(Callable[..., T], wrapper)
    
    return decorator


def handle_api_error(func: Callable[..., T]) -> Callable[..., Optional[T]]:
    """Decorator to handle API errors gracefully.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that returns None on error
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            st.warning(f"Rate limit reached. Please wait a moment and try again.")
            st.toast("Rate limit reached", icon="⚠️")
            logger.warning(f"Rate limit error: {e}")
            return None
        except RetryableError as e:
            st.error(f"Operation failed: {str(e)}")
            st.toast("Operation failed", icon="❌")
            logger.error(f"Retryable error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.toast("Unexpected error", icon="❌")
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return None
    
    return cast(Callable[..., Optional[T]], wrapper)


def parse_error_response(error_message: str) -> tuple[str, bool]:
    """Parse error message to determine if it's retryable.
    
    Args:
        error_message: The error message to parse
        
    Returns:
        Tuple of (cleaned_message, is_retryable)
    """
    error_lower = error_message.lower()
    
    # Check for rate limit errors
    if any(term in error_lower for term in ['rate limit', 'quota', 'too many requests']):
        return "Rate limit exceeded. Please wait before retrying.", True
    
    # Check for temporary errors
    if any(term in error_lower for term in ['timeout', 'temporary', 'try again']):
        return error_message, True
    
    # Check for authentication errors (not retryable)
    if any(term in error_lower for term in ['unauthorized', 'authentication', 'credentials']):
        return error_message, False
    
    # Check for permission errors (not retryable)
    if any(term in error_lower for term in ['permission', 'forbidden', 'access denied']):
        return error_message, False
    
    # Default: not retryable
    return error_message, False


class ErrorContext:
    """Context manager for error handling with user feedback."""
    
    def __init__(self, operation: str, show_spinner: bool = True):
        """Initialize error context.
        
        Args:
            operation: Description of the operation
            show_spinner: Whether to show a spinner
        """
        self.operation = operation
        self.show_spinner = show_spinner
        self.start_time = None
    
    def __enter__(self):
        """Enter the context."""
        self.start_time = time.time()
        if self.show_spinner:
            import streamlit as st
            self.spinner = st.spinner(f"{self.operation}...")
            self.spinner.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and handle any exceptions."""
        if self.show_spinner and hasattr(self, 'spinner'):
            self.spinner.__exit__(exc_type, exc_val, exc_tb)
        
        if exc_type is not None:
            elapsed = time.time() - self.start_time
            logger.error(f"{self.operation} failed after {elapsed:.2f}s: {exc_val}")
            
            if isinstance(exc_val, (RetryableError, RateLimitError)):
                st.warning(f"{self.operation} failed: {exc_val}. Please try again.")
            else:
                st.error(f"{self.operation} failed: {exc_val}")
            
            # Suppress the exception (we've handled it)
            return True
        
        return False