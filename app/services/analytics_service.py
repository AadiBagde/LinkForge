# Analytics service

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models


def get_url_analytics(db: Session, short_code: str):

    url = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()

    if not url:
        return None

    total_clicks = db.query(models.Click).filter(
        models.Click.url_id == url.id
    ).count()

    return {
        "original_url": url.original_url,
        "created_at": url.created_at,
        "total_clicks": total_clicks
    }


# NEW: Top URLs analytics
def get_top_urls(db: Session, limit: int = 10):

    results = (
        db.query(
            models.URL.short_code,
            func.count(models.Click.id).label("clicks")
        )
        .join(models.Click)
        .group_by(models.URL.short_code)
        .order_by(func.count(models.Click.id).desc())
        .limit(limit)
        .all()
    )

    return results