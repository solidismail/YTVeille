"""
Persistance des vidéos dans un fichier JSON.
Écriture atomique pour éviter la corruption.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_PATH = Path(os.environ.get("DATA_PATH", "/app/data/videos.json"))
CONFIG_PATH = DATA_PATH.parent / "config.json"
QUOTA_PATH = DATA_PATH.parent / "quota_status.json"

DEFAULT_QUERIES = [
    "Kubernetes production français",
    "Kubernetes architecture français",
    "Kubernetes retour d'expérience",
    "Kubernetes incident production français",
    "Kubernetes scaling français",
    "Kubernetes observabilité",
    "Kubernetes tutoriel français",
    "Kubernetes déploiement français",
]


def _ensure_dir() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_quota_status() -> dict:
    """Charge l'état du quota YouTube API."""
    if not QUOTA_PATH.exists():
        return {"exceeded": False, "exceeded_at": None}
    with QUOTA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_quota_status(exceeded: bool) -> None:
    """Persiste l'état du quota YouTube API."""
    _ensure_dir()
    tmp = QUOTA_PATH.with_suffix(".tmp")
    data = {
        "exceeded": exceeded,
        "exceeded_at": datetime.now(timezone.utc).isoformat() if exceeded else None,
    }
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    tmp.replace(QUOTA_PATH)


def load_config() -> dict:
    """Charge la configuration de recherche (queries)."""
    if not CONFIG_PATH.exists():
        return {"queries": DEFAULT_QUERIES}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Sauvegarde la configuration de recherche."""
    _ensure_dir()
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    tmp.replace(CONFIG_PATH)


def load_videos() -> list[dict[str, Any]]:
    """Charge la liste des vidéos depuis le fichier JSON."""
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_videos(videos: list[dict[str, Any]]) -> None:
    """Sauvegarde atomique des vidéos (écriture via fichier temporaire)."""
    _ensure_dir()
    tmp = DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2, default=str)
    tmp.replace(DATA_PATH)


def get_last_updated() -> datetime | None:
    """Retourne la date de dernière modification du fichier de données."""
    if not DATA_PATH.exists():
        return None
    return datetime.fromtimestamp(DATA_PATH.stat().st_mtime)
