"""
Authentication endpoints for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.database import get_db
from app.core.security import get_current_user, JWTHandler
from app.core.config import settings
from app.core.logging_config import get_logger
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    AuthResponse,
    TokenResponse,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_id,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Register new user")
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: User email (must be unique)
    - **username**: User username (must be unique)
    - **password**: Password (min 8 chars, must include uppercase, lowercase, numbers)
    
    Returns: User info and access token
    """
    
    try:
        # Create user
        user = create_user(
            db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password
        )
        
        # Create access token
        access_token = create_access_token(user.id)
        
        logger.info(f"User registered successfully: {user.username}")
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=AuthResponse, summary="Login user")
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    - **email**: User email
    - **password**: User password
    
    Returns: User info and access token
    """
    
    try:
        # Authenticate user
        user = authenticate_user(
            db,
            email=credentials.email,
            password=credentials.password
        )
        
        # Create access token
        access_token = create_access_token(user.id)
        
        logger.info(f"User logged in: {user.username}")
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Requires: Valid JWT token in Authorization header
    
    Returns: Current user information
    """
    
    try:
        user_id = int(current_user.get("sub"))
        user = get_user_by_id(db, user_id)
        
        if not user:
            logger.warning(f"User not found for ID in token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
    except ValueError:
        logger.error("Invalid user ID in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
