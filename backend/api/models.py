from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Video(BaseModel):
    id: str
    title: str
    channel: str
    published_at: datetime
    duration_seconds: int
    view_count: int
    like_count: int
    thumbnail_url: str
    youtube_url: str
    tags: List[str] = []
    has_chapters: bool = False
    score: float = 0.0
    topics: List[str] = []


class VideoList(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Video]


class FilterParams(BaseModel):
    min_score: float = 0.0
    topic: Optional[str] = None
    days: int = 30
    page: int = 1
    page_size: int = 20


class RefreshRequest(BaseModel):
    queries: Optional[List[str]] = None


class RefreshResult(BaseModel):
    fetched: int
    scored: int
    stored: int
    timestamp: datetime
