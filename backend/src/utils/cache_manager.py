import logging
import time
import asyncio
import functools
from typing import Any, Dict, Callable, Optional, TypeVar, Generic, Union

# Type variables for generic caching
K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type
F = TypeVar('F', bound=Callable)  # Function type

# Configure logger
logger = logging.getLogger(__name__)

class CacheManager(Generic[K, V]):
    """
    Generic cache manager for storing data with optional TTL
    
    This class provides a standardized caching mechanism that can be used
    across the application to reduce duplicate cache implementations.
    """
    
    def __init__(self, ttl: Optional[int] = None, name: str = "default"):
        """
        Initialize cache with optional TTL
        
        Args:
            ttl (Optional[int]): Time-to-live in seconds (None for no expiration)
            name (str): Name for this cache instance (for logging)
        """
        self.cache = {}  # Dict to store cached values
        self.timestamps = {}  # Dict to store timestamps for TTL
        self.ttl = ttl  # Time-to-live in seconds
        self.name = name
        logger.debug(f"Initialized cache manager: {name}")
    
    def get(self, key: K) -> Optional[V]:
        """
        Get value from cache
        
        Args:
            key (K): Cache key
            
        Returns:
            Optional[V]: Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
            
        # Check if expired
        if self.ttl is not None:
            timestamp = self.timestamps.get(key, 0)
            if time.time() - timestamp > self.ttl:
                # Expired, remove from cache
                logger.debug(f"Cache {self.name}: Key {key} expired")
                self._remove(key)
                return None
                
        return self.cache[key]
    
    def set(self, key: K, value: V) -> None:
        """
        Set value in cache
        
        Args:
            key (K): Cache key
            value (V): Value to cache
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
        logger.debug(f"Cache {self.name}: Set key {key}")
    
    def _remove(self, key: K) -> None:
        """
        Remove key from cache
        
        Args:
            key (K): Cache key
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self) -> None:
        """Clear the entire cache"""
        self.cache.clear()
        self.timestamps.clear()
        logger.debug(f"Cache {self.name}: Cleared")
    
    def invalidate(self, key: K) -> None:
        """
        Invalidate a specific key
        
        Args:
            key (K): Cache key to invalidate
        """
        self._remove(key)
        logger.debug(f"Cache {self.name}: Invalidated key {key}")
    
    def cached(self, key_func: Callable = None):
        """
        Decorator for caching function results
        
        Args:
            key_func (Callable, optional): Function to generate cache key from args/kwargs
                If None, a key will be generated from the arguments
                
        Example:
            @cache_manager.cached()
            def expensive_function(arg1, arg2):
                # Function implementation
                
            @cache_manager.cached(lambda *args, **kwargs: f"custom_{args[0]}")
            def another_function(arg1, arg2):
                # Function implementation
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation from args and sorted kwargs
                    key_parts = [str(arg) for arg in args]
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{'_'.join(key_parts)}"
                
                # Check cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache {self.name}: Hit for {func.__name__} with key {cache_key}")
                    return cached_result
                
                # Call function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result)
                logger.debug(f"Cache {self.name}: Miss for {func.__name__}, stored with key {cache_key}")
                
                return result
            
            return wrapper
            
        return decorator
    
    def async_cached(self, key_func: Callable = None):
        """
        Decorator for caching async function results
        
        Args:
            key_func (Callable, optional): Function to generate cache key from args/kwargs
                If None, a key will be generated from the arguments
                
        Example:
            @cache_manager.async_cached()
            async def expensive_async_function(arg1, arg2):
                # Async function implementation
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation from args and sorted kwargs
                    key_parts = [str(arg) for arg in args]
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{'_'.join(key_parts)}"
                
                # Check cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache {self.name}: Hit for {func.__name__} with key {cache_key}")
                    return cached_result
                
                # Call async function
                result = await func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result)
                logger.debug(f"Cache {self.name}: Miss for {func.__name__}, stored with key {cache_key}")
                
                return result
            
            return wrapper
            
        return decorator


# Create cache instances for common use cases
CATEGORY_CACHE = CacheManager(ttl=3600, name="category")  # 1 hour TTL
LLM_RESPONSE_CACHE = CacheManager(ttl=86400, name="llm_response")  # 24 hour TTL
SESSION_CACHE = CacheManager(ttl=1800, name="session")  # 30 minute TTL