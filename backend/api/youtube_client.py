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


def _iso_days_ago(days: int = 90) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
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


_FRENCH_WORDS = {
    "avec", "pour", "dans", "sur", "cette", "votre", "notre", "mais", "très",
    "comme", "nous", "vous", "comment", "voici", "voilà", "pourquoi", "mise",
    "une", "des", "les", "est", "par", "qui", "que", "aux", "tout", "son",
    "leur", "aussi", "bien", "chez", "vers", "sous", "avoir", "être", "faire",
}

_FR_ACCENT_RE = re.compile(r"[éèêëàâùûîïôçœæ]", re.IGNORECASE)


def _is_likely_french(snippet: dict) -> bool:
    """Retourne True si la vidéo est vraisemblablement en français."""
    audio_lang = (snippet.get("defaultAudioLanguage") or "").lower()
    default_lang = (snippet.get("defaultLanguage") or "").lower()
    title = snippet.get("title", "")
    first_desc = (snippet.get("description") or "")[:400]

    # Langue explicitement déclarée française
    if audio_lang.startswith("fr") or default_lang.startswith("fr"):
        return True
    # Accents français dans le titre → signal fort
    if _FR_ACCENT_RE.search(title):
        return True
    # Langue explicitement anglaise (ou autre non-fr) → rejeter
    if audio_lang and not audio_lang.startswith("fr"):
        return False
    if default_lang and not default_lang.startswith("fr"):
        return False
    # Langue inconnue : détecter via accents ou mots français dans la description
    if _FR_ACCENT_RE.search(first_desc):
        return True
    words = set(f"{title} {first_desc}".lower().split())
    return bool(words & _FRENCH_WORDS)


_STOPWORDS = {
    "en", "de", "du", "le", "la", "les", "un", "une", "des", "et", "ou",
    "pour", "sur", "avec", "dans", "par", "au", "aux", "ce", "qui", "que",
    "français", "french", "fr", "how", "to", "the", "and", "with",
}


def _extract_keywords(query: str) -> list[str]:
    """Extrait les mots-clés significatifs d'une requête (mots > 2 chars, hors stopwords)."""
    return [w for w in query.lower().split() if len(w) > 2 and w not in _STOPWORDS]


def _is_relevant(video: dict, source_queries: list[str]) -> bool:
    """Retourne True si au moins un mot-clé de la requête source est dans le titre, les tags ou la description."""
    title = video.get("title", "").lower()
    tags = " ".join(video.get("tags", [])).lower()
    desc = video.get("_desc_preview", "").lower()
    text = f"{title} {tags} {desc}"
    for query in source_queries:
        for kw in _extract_keywords(query):
            if kw in text:
                return True
    return False


def _add_french_hint(query: str) -> str:
    """Ajoute 'français' à la requête si aucun indicateur de langue n'est présent."""
    lower = query.lower()
    if any(w in lower for w in ["français", "francais", "french", " fr "]):
        return query
    return f"{query} français"


async def search_videos(query: str, client: httpx.AsyncClient, api_key: str) -> list[str]:
    """Retourne une liste d'IDs vidéos pour une requête donnée."""
    params = {
        "part": "id",
        "q": _add_french_hint(query),
        "type": "video",
        "relevanceLanguage": "fr",
        "regionCode": "FR",
        "publishedAfter": _iso_days_ago(90),
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

        if not _is_likely_french(snippet):
            continue

        title = snippet.get("title", "")
        videos.append({
            "id": item["id"],
            "title": title,
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "duration_seconds": duration_s,
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "youtube_url": f"https://www.youtube.com/watch?v={item['id']}",
            "tags": snippet.get("tags", [])[:20],
            "has_chapters": _has_chapters(description),
            "_desc_preview": description[:600],  # temporaire, nettoyé après filtrage
        })

    return videos


async def fetch_all_videos(queries: list[str] | None = None) -> list[dict[str, Any]]:
    """Lance la recherche sur tous les mots-clés, déduplique par ID et tracke les requêtes sources."""
    if queries is None:
        queries = SEARCH_QUERIES
    api_key = _get_api_key()

    # Map video_id → liste des requêtes qui l'ont renvoyé
    id_to_queries: dict[str, list[str]] = {}

    async with httpx.AsyncClient() as client:
        for query in queries:
            try:
                ids = await search_videos(query, client, api_key)
                for vid_id in ids:
                    id_to_queries.setdefault(vid_id, []).append(query)
                logger.info("Requête '%s' → %d IDs", query, len(ids))
            except QuotaExceededError:
                logger.warning("Quota YouTube dépassé — arrêt des requêtes restantes")
                raise
            except Exception as exc:
                logger.error("Erreur pour la requête '%s': %s", query, exc)

        if not id_to_queries:
            return []

        all_videos = await get_video_details(list(id_to_queries.keys()), client, api_key)

    # Attacher les requêtes sources à chaque vidéo
    for video in all_videos:
        video["source_queries"] = id_to_queries.get(video["id"], [])

    # Filtrer les vidéos non pertinentes (titre/tags/description sans aucun mot-clé de la requête)
    before = len(all_videos)
    all_videos = [v for v in all_videos if _is_relevant(v, v["source_queries"])]
    logger.info("Filtre pertinence : %d → %d vidéos", before, len(all_videos))

    # Supprimer le champ temporaire avant persistance
    for v in all_videos:
        v.pop("_desc_preview", None)

    return all_videos
