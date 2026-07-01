# URL endpoints and routing

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db, SessionLocal
from app.db import models
from app.core.config import settings
from app.core.logging_config import get_logger

from app.services.shortener_service import (
    create_short_url,
    get_url_by_short_code
)

from app.services.qr_service import generate_qr
from app.services.analytics_service import get_url_analytics, get_top_urls
from app.services.cache_service import get_cached_url, cache_url, invalidate_cache
from app.services.rate_limit_service import check_rate_limit
from app.services.geo_service import get_location
from app.services.device_service import parse_device_from_user_agent

from app.schemas import URLCreate, URLResponse, URLAnalytics

logger = get_logger(__name__)
router = APIRouter()


def log_click_background(url_id: int, ip_address: str, user_agent: str, referrer: str):
    """Background task to log click analytics with device info"""
    db = SessionLocal()
    try:
        country, city = get_location(ip_address)
        
        # Parse device info from User-Agent
        device_info = parse_device_from_user_agent(user_agent)
        
        click = models.Click(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city,
            browser=device_info.browser_name,
            browser_version=device_info.browser_version,
            os_name=device_info.os_name,
            os_version=device_info.os_version,
            device_type=device_info.device_type,
        )
        db.add(click)
        db.commit()
        logger.debug(f"Click logged for URL {url_id} from {ip_address} ({device_info.device_type})")
    except Exception as e:
        logger.error(f"Background task failed to log click: {str(e)}")
    finally:
        db.close()


@router.post("/shorten", response_model=URLResponse, tags=["URLs"], summary="Create shortened URL")
def shorten_url(
    payload: URLCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a shortened URL.
    
    - **original_url**: The URL to shorten (required)
    - **custom_code**: Optional custom short code
    - **expires_at**: Optional expiration date
    
    Returns the shortened URL.
    """
    
    check_rate_limit(request.client.host)

    try:
        short_code = create_short_url(
            db,
            str(payload.original_url),
            payload.custom_code,
            expires_at=payload.expires_at
        )

        logger.info(
            f"URL shortened: {short_code}",
            extra={"client": request.client.host, "short_code": short_code}
        )

        return URLResponse(
            short_url=f"{settings.BASE_URL}/{short_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error shortening URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shortened URL"
        )


@router.get("/analytics/top", tags=["Analytics"], summary="Get top URLs")
def top_urls(request: Request, db: Session = Depends(get_db)):
    """
    Get the most clicked shortened URLs.
    
    Returns top 10 URLs ranked by click count.
    """
    
    check_rate_limit(request.client.host)
    
    try:
        results = get_top_urls(db)
        logger.debug("Top URLs retrieved")
        return results
    except Exception as e:
        logger.error(f"Error retrieving top URLs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top URLs"
        )


@router.get("/analytics/{short_code}", response_model=URLAnalytics, tags=["Analytics"], summary="Get URL analytics")
def get_analytics(short_code: str, request: Request, db: Session = Depends(get_db)):
    """
    Get analytics for a specific shortened URL.
    
    Returns: original URL, creation date, and total clicks.
    """
    
    check_rate_limit(request.client.host)

    try:
        analytics = get_url_analytics(db, short_code)

        if not analytics:
            logger.warning(f"Analytics requested for non-existent URL: {short_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        logger.debug(f"Analytics returned for {short_code}")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/qr/{short_code}", tags=["URLs"], summary="Generate QR code")
def get_qr(short_code: str, request: Request, db: Session = Depends(get_db)):
    """
    Generate a QR code for a shortened URL.
    
    Returns: PNG image of the QR code
    """
    
    check_rate_limit(request.client.host)

    try:
        url = get_url_by_short_code(db, short_code)

        if not url:
            logger.warning(f"QR code requested for non-existent URL: {short_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        qr_code = generate_qr(f"{settings.BASE_URL}/{short_code}")
        logger.debug(f"QR code generated for {short_code}")

        return Response(content=qr_code, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code"
        )


@router.get("/{short_code}", tags=["URLs"], summary="Redirect to original URL")
def redirect_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Redirect to the original URL and log click analytics.
    
    Returns: 307 Temporary Redirect
    """
    
    check_rate_limit(request.client.host)

    try:
        # Try cache first
        cached_url = get_cached_url(short_code)

        if cached_url:
            url = get_url_by_short_code(db, short_code)

            if not url:
                logger.warning(f"Cache hit but URL not found in DB: {short_code}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="URL not found"
                )

            # Check expiration
            if url.expires_at and datetime.now(timezone.utc) > url.expires_at:
                logger.info(f"Expired URL accessed: {short_code}")
                invalidate_cache(short_code)
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="This link has expired"
                )

            background_tasks.add_task(
                log_click_background,
                url_id=url.id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                referrer=request.headers.get("referer", "")
            )

            logger.info(
                f"Redirect (cache hit): {short_code}",
                extra={"client": request.client.host, "cache": "hit"}
            )
            return RedirectResponse(url=cached_url, status_code=307)

        # Cache miss - query database
        url = get_url_by_short_code(db, short_code)

        if not url:
            logger.warning(f"Redirect requested for non-existent URL: {short_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        # Check expiration
        if url.expires_at and datetime.now(timezone.utc) > url.expires_at:
            logger.info(f"Expired URL accessed: {short_code}")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This link has expired"
            )

        # Cache the URL for future requests
        cache_url(short_code, url.original_url)

        background_tasks.add_task(
            log_click_background,
            url_id=url.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            referrer=request.headers.get("referer", "")
        )

        logger.info(
            f"Redirect (cache miss): {short_code}",
            extra={"client": request.client.host, "cache": "miss"}
        )

        return RedirectResponse(
            url=url.original_url,
            status_code=307
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing redirect: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process redirect"
        )