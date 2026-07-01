"""
Security utilities for LinkForge.
Includes JWT token generation/validation and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import logging

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {str(e)}")
        return False


# JWT utilities
class JWTHandler:
    """Handle JWT token generation and validation"""
    
    # These should be in settings
    SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    @classmethod
    def create_access_token(
        cls,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        try:
            import jwt
        except ImportError:
            logger.error("PyJWT not installed. Install with: pip install python-jose")
            raise ImportError("PyJWT required for JWT functionality")
        
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                cls.SECRET_KEY,
                algorithm=cls.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create JWT token: {str(e)}")
            raise
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            import jwt
        except ImportError:
            logger.error("PyJWT not installed. Install with: pip install python-jose")
            raise ImportError("PyJWT required for JWT functionality")
        
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {str(e)}")
            return None


# Security dependency
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to extract and validate current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Token payload with user info
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    payload = JWTHandler.verify_token(token)
    
    if not payload:
        logger.warning(f"Authentication failed: Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Optional dependency for public endpoints that have auth benefits.
    Returns None if no credentials provided, raises exception if invalid.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        Token payload if provided and valid, None otherwise
    """
    if not credentials:
        return None
    
    return await get_current_user(credentials)
