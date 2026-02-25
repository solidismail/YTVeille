"""
Worker cron — Veille YouTube Kubernetes.
Mise à jour quotidienne à 6h UTC via APScheduler.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Ajout du répertoire parent au path Python
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.storage import save_videos, load_config
from api.youtube_client import fetch_all_videos
from scoring.scorer import score_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """Pipeline complet : fetch → score → persist."""
    logger.info("=== Démarrage du pipeline de mise à jour ===")
    start = datetime.now(timezone.utc)

    try:
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

        scored.sort(key=lambda x: x["score"], reverse=True)
        save_videos(scored)

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(
            "=== Pipeline terminé : %d vidéos en %.1f secondes ===",
            len(scored),
            elapsed,
        )
    except Exception as exc:
        logger.error("Erreur pipeline : %s", exc, exc_info=True)


if __name__ == "__main__":
    # Exécution immédiate au démarrage puis cron quotidien
    logger.info("Worker démarré — exécution immédiate puis cron à 6h UTC")
    run_pipeline()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_refresh",
        name="Mise à jour quotidienne des vidéos",
    )
    logger.info("Scheduler configuré : cron 6h00 UTC")
    scheduler.start()
