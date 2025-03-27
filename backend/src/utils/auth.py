import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.environment import Environment
import logging

# Configure logger
logger = logging.getLogger(__name__)

env = Environment()
security = HTTPBearer()

class AuthUtils:
    """
    Utilities for Supabase JWT authentication
    """
    
    @staticmethod
    async def get_user_id_from_token(token: str) -> str:
        """
        Extract and validate user ID from Supabase JWT
        
        Args:
            token (str): JWT token
            
        Returns:
            str: User ID
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode token with verification using the JWT secret
            decoded = jwt.decode(
                token, 
                env.get("supabase_jwt_secret"), 
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # Supabase stores the user ID in the 'sub' claim
            user_id = decoded.get('sub')
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
                
            return user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.PyJWTError as e:
            logger.error(f"JWT verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token format")

    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """
        FastAPI dependency to extract current user from request
        
        Args:
            credentials: HTTP Authorization header
            
        Returns:
            str: User ID
        """
        token = credentials.credentials
        return await AuthUtils.get_user_id_from_token(token)

# Simplified dependency for routes
get_current_user = AuthUtils.get_current_user