from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class URLAnalytics(BaseModel):
    original_url: str
    created_at: datetime
    total_clicks: int


class URLCreate(BaseModel):
    original_url: HttpUrl
    expires_at: Optional[str] = None
    custom_code: Optional[str] = None   # NEW


class URLResponse(BaseModel):
    short_url: str