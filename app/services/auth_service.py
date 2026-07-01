"""
Authentication service for user registration and login.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta

from app.db import models
from app.core.security import hash_password, verify_password, JWTHandler
from app.core.validators import validate_email, validate_password
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def create_user(db: Session, email: str, username: str, password: str) -> models.User:
    """
    Create a new user account.
    
    Args:
        db: Database session
        email: User email
        username: User username
        password: Plain text password
        
    Returns:
        Created User model
        
    Raises:
        HTTPException: If email/username already exists or validation fails
    """
    
    # Validate inputs
    email = validate_email(email)
    password = validate_password(password)
    
    if len(username) < 3 or len(username) > 50:
        logger.warning(f"Invalid username length: {username}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be between 3 and 50 characters"
        )
    
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == username)
    ).first()
    
    if existing_user:
        logger.warning(f"User registration attempt with existing email/username: {email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = hash_password(password)
    
    new_user = models.User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user created: {username} ({email})", extra={"user_id": new_user.id})
    
    return new_user


def authenticate_user(db: Session, email: str, password: str) -> models.User:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        Authenticated User model
        
    Raises:
        HTTPException: If credentials are invalid
    """
    
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    logger.info(f"User authenticated: {email}", extra={"user_id": user.id})
    
    return user


def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token for user.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    
    data = {"sub": str(user_id), "type": "access"}
    
    token = JWTHandler.create_access_token(data, expires_delta)
    
    logger.debug(f"Access token created for user {user_id}")
    
    return token


def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User model or None
    """
    
    return db.query(models.User).filter(models.User.id == user_id).first()
