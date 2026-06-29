# URL endpoints and routing

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.db import models

from app.services.shortener_service import (
    create_short_url,
    get_url_by_short_code
)

from app.services.qr_service import generate_qr
from app.services.analytics_service import get_url_analytics, get_top_urls
from app.services.cache_service import get_cached_url, cache_url
from app.services.rate_limit_service import check_rate_limit
from app.services.geo_service import get_location

from app.schemas import URLCreate, URLResponse, URLAnalytics


router = APIRouter()


def log_click_background(url_id: int, ip_address: str, user_agent: str, referrer: str):
    db = SessionLocal()
    try:
        country, city = get_location(ip_address)
        click = models.Click(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city
        )
        db.add(click)
        db.commit()
    except Exception as e:
        print(f"Background task failed: {e}")
    finally:
        db.close()


@router.post("/shorten", response_model=URLResponse)
def shorten_url(
    payload: URLCreate,
    request: Request,
    db: Session = Depends(get_db)
):

    check_rate_limit(request.client.host)

    short_code = create_short_url(
    db,
    str(payload.original_url),
    payload.custom_code
    )

    return URLResponse(
        short_url=f"http://localhost:8000/{short_code}"
    )


@router.get("/analytics/top")
def top_urls(db: Session = Depends(get_db)):

    results = get_top_urls(db)

    return [
        {
            "short_code": r.short_code,
            "clicks": r.clicks
        }
        for r in results
    ]


@router.get("/analytics/{short_code}", response_model=URLAnalytics)
def get_analytics(short_code: str, db: Session = Depends(get_db)):

    analytics = get_url_analytics(db, short_code)

    if not analytics:
        raise HTTPException(status_code=404, detail="URL not found")

    return analytics


@router.get("/qr/{short_code}")
def get_qr(short_code: str, db: Session = Depends(get_db)):

    url = get_url_by_short_code(db, short_code)

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    qr_code = generate_qr(f"http://localhost:8000/{short_code}")

    return Response(content=qr_code, media_type="image/png")


@router.get("/{short_code}")
def redirect_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    cached_url = get_cached_url(short_code)

    # ---------- Cache Hit ----------
    if cached_url:

        url = get_url_by_short_code(db, short_code)

        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        background_tasks.add_task(
            log_click_background,
            url_id=url.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer")
        )

        return RedirectResponse(url=cached_url, status_code=307)

    # ---------- Cache Miss ----------
    url = get_url_by_short_code(db, short_code)

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    cache_url(short_code, url.original_url)

    background_tasks.add_task(
        log_click_background,
        url_id=url.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )

    return RedirectResponse(
        url=url.original_url,
        status_code=307
    )