from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db import models
from app.utils.base62 import encode
from app.core.logging_config import get_logger
from app.core.validators import validate_custom_code, validate_url
from datetime import datetime
import uuid

logger = get_logger(__name__)


def create_short_url(
    db: Session,
    original_url: str,
    custom_code: str | None = None,
    user_id: int | None = None,
    expires_at: datetime | None = None,
):
    """
    Create a shortened URL.
    
    Args:
        db: Database session
        original_url: The original long URL to shorten
        custom_code: Optional custom short code
        user_id: Optional user ID (for authentication)
        expires_at: Optional expiration datetime
        
    Returns:
        Generated short code
        
    Raises:
        HTTPException: If validation fails or code already exists
    """
    
    # Validate input
    try:
        original_url = validate_url(original_url)
    except Exception as e:
        logger.warning(f"URL validation failed: {str(e)}")
        raise

    # If user provides custom short code
    if custom_code:
        try:
            custom_code = validate_custom_code(custom_code)
        except Exception as e:
            logger.warning(f"Custom code validation failed: {str(e)}")
            raise

        existing = db.query(models.URL).filter(
            models.URL.short_code == custom_code
        ).first()

        if existing:
            logger.warning(f"Custom code collision: {custom_code} already exists")
            raise HTTPException(
                status_code=400,
                detail="Custom short code already exists"
            )

        new_url = models.URL(
            original_url=original_url,
            short_code=custom_code,
            user_id=user_id,
            expires_at=expires_at,
        )

        db.add(new_url)
        db.commit()
        db.refresh(new_url)

        logger.info(
            f"Custom URL created: {custom_code} -> {original_url}",
            extra={"short_code": custom_code, "user_id": user_id}
        )
        return custom_code

    # Default behavior (Base62 ID encoding)
    # Generate a unique temp code to avoid Unique Constraint collision on concurrent requests
    temp_code = f"tmp_{uuid.uuid4().hex[:8]}"
    
    new_url = models.URL(
        original_url=original_url,
        short_code=temp_code,
        user_id=user_id,
        expires_at=expires_at,
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    short_code = encode(new_url.id)

    new_url.short_code = short_code
    db.commit()

    logger.info(
        f"Auto-generated URL created: {short_code} -> {original_url}",
        extra={"short_code": short_code, "user_id": user_id, "url_id": new_url.id}
    )
    return short_code


def get_url_by_short_code(db: Session, short_code: str):
    """
    Retrieve a URL record by short code.
    
    Args:
        db: Database session
        short_code: The short code to look up
        
    Returns:
        URL model instance or None
    """
    return db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()