"""
Client YouTube Data API v3.
Recherche multi-mots-clés de vidéos Kubernetes en français.
"""

import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Levée quand le quota journalier YouTube API est dépassé (HTTP 403)."""

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

SEARCH_QUERIES = [
    "Kubernetes production français",
    "Kubernetes architecture français",
    "Kubernetes retour d'expérience",
    "Kubernetes incident production français",
    "Kubernetes scaling français",
    "Kubernetes observabilité",
    "Kubernetes tutoriel français",
    "Kubernetes déploiement français",
]


def _get_api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY manquante dans les variables d'environnement")
    return key


def _iso_30_days_ago() -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=30)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_duration(iso_duration: str) -> int:
    """Convertit ISO 8601 duration (PT1H2M3S) en secondes."""
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    m = re.match(pattern, iso_duration or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mn * 60 + s


def _has_chapters(description: str) -> bool:
    """Détecte la présence de chapitrage (timestamps 0:00 dans la description)."""
    return bool(re.search(r"^\s*\d+:\d+", description or "", re.MULTILINE))


async def search_videos(query: str, client: httpx.AsyncClient, api_key: str) -> list[str]:
    """Retourne une liste d'IDs vidéos pour une requête donnée."""
    params = {
        "part": "id",
        "q": query,
        "type": "video",
        "relevanceLanguage": "fr",
        "regionCode": "FR",
        "publishedAfter": _iso_30_days_ago(),
        "maxResults": 25,
        "key": api_key,
    }
    resp = await client.get(f"{YOUTUBE_API_BASE}/search", params=params, timeout=15.0)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise QuotaExceededError("Quota YouTube API journalier dépassé (HTTP 403)") from e
        raise
    data = resp.json()
    return [item["id"]["videoId"] for item in data.get("items", [])]


async def get_video_details(video_ids: list[str], client: httpx.AsyncClient, api_key: str) -> list[dict[str, Any]]:
    """Retourne les détails enrichis pour une liste d'IDs vidéos."""
    if not video_ids:
        return []

    # Batches de 50 (limite API)
    results = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(batch),
            "key": api_key,
        }
        resp = await client.get(f"{YOUTUBE_API_BASE}/videos", params=params, timeout=15.0)
        resp.raise_for_status()
        results.extend(resp.json().get("items", []))

    videos = []
    for item in results:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        details = item.get("contentDetails", {})

        duration_s = _parse_duration(details.get("duration", ""))
        description = snippet.get("description", "")

        videos.append({
            "id": item["id"],
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "duration_seconds": duration_s,
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "youtube_url": f"https://www.youtube.com/watch?v={item['id']}",
            "tags": snippet.get("tags", [])[:20],
            "has_chapters": _has_chapters(description),
        })

    return videos


async def fetch_all_videos(queries: list[str] | None = None) -> list[dict[str, Any]]:
    """Lance la recherche sur tous les mots-clés et déduplique par ID."""
    if queries is None:
        queries = SEARCH_QUERIES
    api_key = _get_api_key()
    seen_ids: set[str] = set()
    all_videos: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        for query in queries:
            try:
                ids = await search_videos(query, client, api_key)
                new_ids = [vid_id for vid_id in ids if vid_id not in seen_ids]
                seen_ids.update(new_ids)
                details = await get_video_details(new_ids, client, api_key)
                all_videos.extend(details)
                logger.info("Requête '%s' → %d vidéos", query, len(details))
            except QuotaExceededError:
                logger.warning("Quota YouTube dépassé — arrêt des requêtes restantes")
                raise
            except Exception as exc:
                logger.error("Erreur pour la requête '%s': %s", query, exc)

    return all_videos
