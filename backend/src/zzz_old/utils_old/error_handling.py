# backend/src/utils/error_handling.py
import logging
import functools
import traceback
import asyncio
from typing import Callable, TypeVar, Any, Optional, Dict, Type, Union

# Type variable for decorated function
F = TypeVar('F', bound=Callable)

# Configure logger
logger = logging.getLogger(__name__)

class AppError(Exception):
    """
    Base exception class for application-specific errors
    """
    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationError(AppError):
    """Exception for input validation errors"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, status_code=400, details=details)


class ResourceNotFoundError(AppError):
    """Exception for resource not found errors"""
    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, status_code=404)


class AuthorizationError(AppError):
    """Exception for authorization errors"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class ErrorHandler:
    """
    Utility class for standardized error handling
    """
    
    @staticmethod
    def handle_errors(func=None, *, default_message="An unexpected error occurred", 
                      error_map=None, log_traceback=True, reraise=True):
        """
        Decorator to handle errors with specific handlers
        
        Args:
            func: The function to decorate (None if used with parameters)
            default_message (str): Default error message
            error_map (Dict[Type[Exception], Callable]): Mapping of exception types to handler functions
            log_traceback (bool): Whether to log full traceback
            reraise (bool): Whether to re-raise the exception after handling
            
        Example:
            @ErrorHandler.handle_errors(
                error_map={
                    ValueError: lambda e: {"error": str(e), "type": "validation"},
                    TypeError: lambda e: {"error": str(e), "type": "type_error"}
                }
            )
            def my_function():
                # Function implementation
        """
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    # Log the error
                    if log_traceback:
                        logger.error(
                            f"Error in {fn.__name__}: {str(e)}\n"
                            f"{traceback.format_exc()}"
                        )
                    else:
                        logger.error(f"Error in {fn.__name__}: {str(e)}")
                    
                    # Handle specific errors
                    if error_map and type(e) in error_map:
                        handler = error_map[type(e)]
                        result = handler(e)
                        if not reraise:
                            return result
                    
                    # Re-raise the exception if requested
                    if reraise:
                        raise
                    
                    # Return default error if not re-raising
                    return {"error": default_message}
            
            return wrapper
        
        # Direct decoration without arguments
        if func is not None:
            return decorator(func)
        
        # Decoration with arguments
        return decorator
    
    @staticmethod
    def handle_async_errors(func=None, *, default_message="An unexpected error occurred", 
                          error_map=None, log_traceback=True, reraise=True):
        """
        Decorator to handle errors in async functions
        
        Args:
            func: The function to decorate (None if used with parameters)
            default_message (str): Default error message
            error_map (Dict[Type[Exception], Callable]): Mapping of exception types to handler functions
            log_traceback (bool): Whether to log full traceback
            reraise (bool): Whether to re-raise the exception after handling
            
        Example:
            @ErrorHandler.handle_async_errors(
                error_map={
                    ValueError: lambda e: {"error": str(e), "type": "validation"},
                    TypeError: lambda e: {"error": str(e), "type": "type_error"}
                }
            )
            async def my_async_function():
                # Async function implementation
        """
        def decorator(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    # Log the error
                    if log_traceback:
                        logger.error(
                            f"Error in async {fn.__name__}: {str(e)}\n"
                            f"{traceback.format_exc()}"
                        )
                    else:
                        logger.error(f"Error in async {fn.__name__}: {str(e)}")
                    
                    # Handle specific errors
                    if error_map and type(e) in error_map:
                        handler = error_map[type(e)]
                        result = handler(e)
                        if not reraise:
                            return result
                    
                    # Re-raise the exception if requested
                    if reraise:
                        raise
                    
                    # Return default error if not re-raising
                    return {"error": default_message}
            
            return wrapper
        
        # Direct decoration without arguments
        if func is not None:
            return decorator(func)
        
        # Decoration with arguments
        return decorator
    
    @staticmethod
    def default_error_response(e: Exception) -> Dict:
        """
        Default error response handler
        
        Args:
            e (Exception): Exception to handle
            
        Returns:
            Dict: Standardized error response
        """
        # Handle AppError with proper status code
        if isinstance(e, AppError):
            return {
                "error": e.message,
                "status_code": e.status_code,
                "details": e.details
            }
        
        # Handle other exceptions
        return {
            "error": str(e),
            "status_code": 500,
            "details": None
        }

# Add compatibility function for existing code
def async_handle_errors(func=None, **kwargs):
    """
    Compatibility wrapper for ErrorHandler.handle_async_errors
    
    This function provides backward compatibility for code that imports
    async_handle_errors directly.
    """
    if func is None:
        return lambda f: ErrorHandler.handle_async_errors(**kwargs)(f)
    return ErrorHandler.handle_async_errors()(func)