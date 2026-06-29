from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db import models
from app.utils.base62 import encode
import uuid


def create_short_url(
    db: Session,
    original_url: str,
    custom_code: str | None = None
):

    # If user provides custom short code
    if custom_code:

        existing = db.query(models.URL).filter(
            models.URL.short_code == custom_code
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Custom short code already exists"
            )

        new_url = models.URL(
            original_url=original_url,
            short_code=custom_code
        )

        db.add(new_url)
        db.commit()
        db.refresh(new_url)

        return custom_code

    # Default behavior (Base62 ID encoding)
    # Generate a unique temp code to avoid Unique Constraint collision on concurrent requests
    temp_code = f"tmp_{uuid.uuid4().hex[:8]}"
    
    new_url = models.URL(
        original_url=original_url,
        short_code=temp_code
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    short_code = encode(new_url.id)

    new_url.short_code = short_code
    db.commit()

    return short_code


def get_url_by_short_code(db: Session, short_code: str):
    return db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()