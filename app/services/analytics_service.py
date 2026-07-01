# Analytics service

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_url_analytics(db: Session, short_code: str):
    """
    Get analytics for a specific URL.
    
    Args:
        db: Database session
        short_code: Short code to get analytics for
        
    Returns:
        Analytics dict with: original_url, created_at, total_clicks, or None
    """
    
    try:
        url = db.query(models.URL).filter(
            models.URL.short_code == short_code
        ).first()

        if not url:
            logger.debug(f"Analytics requested for non-existent URL: {short_code}")
            return None

        total_clicks = db.query(models.Click).filter(
            models.Click.url_id == url.id
        ).count()

        logger.debug(
            f"Analytics retrieved for {short_code}",
            extra={"short_code": short_code, "clicks": total_clicks}
        )

        return {
            "original_url": url.original_url,
            "created_at": url.created_at,
            "total_clicks": total_clicks
        }
    except Exception as e:
        logger.error(f"Error retrieving analytics for {short_code}: {str(e)}")
        return None


def get_top_urls(db: Session, limit: int = 10):
    """
    Get top URLs ranked by click count.
    
    Args:
        db: Database session
        limit: Maximum number of results (default 10)
        
    Returns:
        List of dicts with short_code and clicks
    """
    
    try:
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

        logger.debug(f"Retrieved top {limit} URLs")
        
        return [
            {"short_code": r.short_code, "clicks": r.clicks}
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error retrieving top URLs: {str(e)}")
        return []