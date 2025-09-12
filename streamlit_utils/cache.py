"""
Caching utilities for Google Group Maker Streamlit app.
"""

import streamlit as st
import hashlib
import time
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
import logging

from streamlit_utils.config import CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def cached_list_groups(_api_instance, query: Optional[str] = None, 
                      domain: Optional[str] = None,
                      max_results: int = 100) -> Optional[List[Dict[str, str]]]:
    """Cached version of list_groups API call.
    
    Args:
        _api_instance: API instance (not hashed due to leading underscore)
        query: Optional search query
        domain: Optional domain filter
        max_results: Maximum number of results
        
    Returns:
        List of groups or None on error
    """
    try:
        return _api_instance.list_groups(query, domain, max_results)
    except Exception as e:
        logger.error(f"Failed to list groups: {e}")
        return None


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def cached_list_members(_api_instance, group_name: str, 
                       include_derived: bool = False,
                       max_results: int = 100) -> Optional[List[Dict[str, str]]]:
    """Cached version of list_members API call.
    
    Args:
        _api_instance: API instance (not hashed due to leading underscore)
        group_name: Name or email of the group
        include_derived: Whether to include nested group members
        max_results: Maximum number of results
        
    Returns:
        List of members or None on error
    """
    try:
        return _api_instance.list_members(group_name, include_derived, max_results)
    except Exception as e:
        logger.error(f"Failed to list members for {group_name}: {e}")
        return None


def clear_group_cache() -> None:
    """Clear all group-related caches."""
    # Clear Streamlit's cache for group functions
    cached_list_groups.clear()
    logger.info("Cleared group list cache")


def clear_member_cache(group_name: Optional[str] = None) -> None:
    """Clear member cache for a specific group or all groups.
    
    Args:
        group_name: Optional group name to clear cache for
    """
    if group_name:
        # Streamlit doesn't support selective cache clearing by parameters
        # So we clear all member caches
        cached_list_members.clear()
        logger.info(f"Cleared member cache for {group_name}")
    else:
        cached_list_members.clear()
        logger.info("Cleared all member caches")


def clear_all_caches() -> None:
    """Clear all application caches."""
    cached_list_groups.clear()
    cached_list_members.clear()
    logger.info("Cleared all caches")


class CacheManager:
    """Manages application-level caching with TTL."""
    
    def __init__(self):
        """Initialize the cache manager."""
        if 'cache_storage' not in st.session_state:
            st.session_state.cache_storage = {}
    
    @staticmethod
    def _get_cache_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Hash string for cache key
        """
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        cache = st.session_state.get('cache_storage', {})
        
        if key in cache:
            entry = cache[key]
            if time.time() - entry['timestamp'] < entry['ttl']:
                logger.debug(f"Cache hit for key: {key}")
                return entry['value']
            else:
                # Expired, remove it
                del cache[key]
                logger.debug(f"Cache expired for key: {key}")
        
        return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
        """Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if 'cache_storage' not in st.session_state:
            st.session_state.cache_storage = {}
        
        st.session_state.cache_storage[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        logger.debug(f"Cached value for key: {key} with TTL: {ttl}s")
    
    @staticmethod
    def clear(pattern: Optional[str] = None) -> None:
        """Clear cache entries matching a pattern.
        
        Args:
            pattern: Optional pattern to match keys (substring match)
        """
        if 'cache_storage' not in st.session_state:
            return
        
        cache = st.session_state.cache_storage
        
        if pattern:
            keys_to_delete = [k for k in cache.keys() if pattern in k]
            for key in keys_to_delete:
                del cache[key]
            logger.info(f"Cleared {len(keys_to_delete)} cache entries matching '{pattern}'")
        else:
            st.session_state.cache_storage = {}
            logger.info("Cleared all cache entries")


def with_cache(ttl: int = CACHE_TTL_SECONDS) -> Callable:
    """Decorator for caching function results with TTL.
    
    Args:
        ttl: Time to live in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_mgr = CacheManager()
            
            # Generate cache key
            cache_key = f"{func.__name__}_{cache_mgr._get_cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_value = cache_mgr.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_mgr.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator