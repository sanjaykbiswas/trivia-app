from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from typing import Optional
import logging
import traceback

from ..dependencies import get_user_service
from ..schemas.user import (
    UserCreateRequest, UserResponse, UserUpdateRequest,
    UserLoginRequest, UserAuthRequest, UserConvertRequest
)
from ...services.user_service import UserService
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    
    Args:
        user_data: Data for creating the user
        user_service: User service dependency
        
    Returns:
        Newly created user
    """
    try:
        user = await user_service.create_user(
            displayname=user_data.displayname,
            email=user_data.email,
            is_temporary=user_data.is_temporary,
            auth_provider=user_data.auth_provider,
            auth_id=user_data.auth_id
        )
        
        return user
        
    except ValueError as e:
        logger.warning(f"Validation error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="ID of the user"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get a user by ID.
    
    Args:
        user_id: ID of the user to retrieve
        user_service: User service dependency
        
    Returns:
        User data
    """
    try:
        user = await user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str = Path(..., description="ID of the user"),
    user_data: UserUpdateRequest = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update a user.
    
    Args:
        user_id: ID of the user to update
        user_data: Data for updating the user
        user_service: User service dependency
        
    Returns:
        Updated user data
    """
    try:
        updated_user = await user_service.update_user(
            user_id=user_id,
            displayname=user_data.displayname,
            email=user_data.email,
            is_temporary=user_data.is_temporary,
            auth_provider=user_data.auth_provider,
            auth_id=user_data.auth_id
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return updated_user
        
    except ValueError as e:
        logger.warning(f"Validation error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: str = Path(..., description="ID of the user"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete a user.
    
    Args:
        user_id: ID of the user to delete
        user_service: User service dependency
        
    Returns:
        Deleted user data
    """
    try:
        deleted_user = await user_service.delete_user(user_id)
        
        if not deleted_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return deleted_user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.post("/auth", response_model=UserResponse)
async def authenticate_user(
    auth_data: UserAuthRequest = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate a user via third-party provider or create if not exists.
    
    Args:
        auth_data: Authentication data
        user_service: User service dependency
        
    Returns:
        User data
    """
    try:
        user, created = await user_service.get_or_create_user_by_auth(
            auth_provider=auth_data.auth_provider,
            auth_id=auth_data.auth_id,
            email=auth_data.email,
            displayname=auth_data.displayname,
            is_temporary=False
        )
        
        return user
        
    except ValueError as e:
        logger.warning(f"Validation error in authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in authentication: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/convert/{user_id}", response_model=UserResponse)
async def convert_temporary_user(
    user_id: str = Path(..., description="ID of the temporary user"),
    convert_data: UserConvertRequest = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Convert a temporary user to a permanent one.
    
    Args:
        user_id: ID of the temporary user
        convert_data: Data for converting the user
        user_service: User service dependency
        
    Returns:
        Updated user data
    """
    try:
        updated_user = await user_service.convert_temporary_user(
            user_id=user_id,
            displayname=convert_data.displayname,
            email=convert_data.email,
            auth_provider=convert_data.auth_provider,
            auth_id=convert_data.auth_id
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return updated_user
        
    except ValueError as e:
        logger.warning(f"Validation error converting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error converting user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert user: {str(e)}"
        )

@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str = Path(..., description="Email address to search for"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get a user by email address.
    
    Args:
        email: Email address to search for
        user_service: User service dependency
        
    Returns:
        User data
    """
    try:
        user = await user_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving user by email {email}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )