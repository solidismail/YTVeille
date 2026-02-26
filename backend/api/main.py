"""
API FastAPI — Veille YouTube Kubernetes.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .models import Video, VideoList, RefreshResult, RefreshRequest
from .storage import load_videos, save_videos, get_last_updated, load_config, save_config, load_quota_status, save_quota_status
from .youtube_client import fetch_all_videos, QuotaExceededError
from scoring.scorer import score_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YTVeille",
    description="API de veille automatique des meilleures vidéos YouTube en français",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_refresh_running = False


def _run_refresh() -> RefreshResult:
    """Pipeline : fetch → score → persist."""
    import asyncio

    config = load_config()
    queries = config.get("queries")
    raw = asyncio.run(fetch_all_videos(queries))
    logger.info("Vidéos récupérées : %d", len(raw))

    scored = []
    for v in raw:
        s, topics = score_video(v)
        v["score"] = s
        v["topics"] = topics
        scored.append(v)

    # Trier par score décroissant
    scored.sort(key=lambda x: x["score"], reverse=True)
    save_videos(scored)
    logger.info("Vidéos sauvegardées : %d", len(scored))

    return RefreshResult(
        fetched=len(raw),
        scored=len(scored),
        stored=len(scored),
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/videos", response_model=VideoList)
def list_videos(
    q: Optional[str] = Query(None),
    min_score: float = Query(0.0, ge=0, le=100),
    topic: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Liste paginée des vidéos avec filtres."""
    all_videos = load_videos()

    # Filtre texte (titre, chaîne, tags YouTube)
    if q:
        q_lower = q.lower()
        all_videos = [
            v for v in all_videos
            if q_lower in v.get("title", "").lower()
            or q_lower in v.get("channel", "").lower()
            or any(q_lower in t.lower() for t in v.get("tags", []))
        ]

    # Filtre score
    filtered = [v for v in all_videos if v.get("score", 0) >= min_score]

    # Filtre topic
    if topic:
        filtered = [v for v in filtered if topic in v.get("topics", [])]

    # Filtre date
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for v in filtered:
        pub = v.get("published_at", "")
        try:
            dt = datetime.fromisoformat(str(pub).replace("Z", "+00:00"))
            if dt >= cutoff:
                result.append(v)
        except Exception:
            result.append(v)

    total = len(result)
    start = (page - 1) * page_size
    page_items = result[start : start + page_size]

    return VideoList(
        total=total,
        page=page,
        page_size=page_size,
        items=[Video(**v) for v in page_items],
    )


@app.get("/api/videos/{video_id}", response_model=Video)
def get_video(video_id: str):
    """Détail d'une vidéo par ID."""
    all_videos = load_videos()
    for v in all_videos:
        if v["id"] == video_id:
            return Video(**v)
    raise HTTPException(status_code=404, detail="Vidéo non trouvée")


@app.get("/api/config")
def get_config():
    """Retourne la configuration de recherche actuelle."""
    return load_config()


@app.post("/api/refresh", response_model=RefreshResult)
def refresh(background_tasks: BackgroundTasks, body: Optional[RefreshRequest] = None):
    """Déclenche une mise à jour. Si body.queries fourni, sauvegarde la config."""
    global _refresh_running
    if _refresh_running:
        raise HTTPException(status_code=409, detail="Un refresh est déjà en cours")
    if body and body.queries:
        save_config({"queries": body.queries})
    _refresh_running = True

    def _wrapped():
        global _refresh_running
        try:
            _run_refresh()
            save_quota_status(False)
        except QuotaExceededError:
            save_quota_status(True)
            logger.warning("Quota YouTube API dépassé — refresh abandonné")
        except Exception as exc:
            logger.error("Erreur lors du refresh : %s", exc)
        finally:
            _refresh_running = False

    background_tasks.add_task(_wrapped)
    return RefreshResult(
        fetched=0,
        scored=0,
        stored=0,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/status")
def status():
    """État de l'API et date de dernière mise à jour."""
    last = get_last_updated()
    videos = load_videos()
    quota = load_quota_status()
    return {
        "status": "ok",
        "video_count": len(videos),
        "last_updated": last.isoformat() if last else None,
        "refresh_running": _refresh_running,
        "queries": load_config().get("queries", []),
        "quota_exceeded": quota.get("exceeded", False),
        "quota_exceeded_at": quota.get("exceeded_at"),
    }
