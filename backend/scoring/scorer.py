"""
Algorithme de scoring des vidéos YouTube Kubernetes.
Score normalisé sur 100.

Critères :
  - Vues pondérées par ancienneté  : 25 pts
  - Ratio likes / vues             : 20 pts
  - Mots-clés techniques détectés  : 25 pts
  - Durée >= 10 min                : 10 pts
  - Présence de chapitrage         : 10 pts
  - Nombre de topics détectés      : 10 pts
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Tuple

from .keywords import TOPIC_KEYWORDS, ADVANCED_KEYWORDS

if TYPE_CHECKING:
    from api.models import Video


def _detect_topics(text: str) -> List[str]:
    """Retourne les topics détectés dans un texte (titre + tags)."""
    text_lower = text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            topics.append(topic)
    return topics


def _keyword_score(text: str) -> float:
    """Score basé sur les mots-clés techniques (0-25)."""
    text_lower = text.lower()
    # Nombre de mots-clés avancés trouvés
    advanced_hits = sum(1 for kw in ADVANCED_KEYWORDS if kw in text_lower)
    # Nombre de mots-clés totaux
    from .keywords import ALL_KEYWORDS
    total_hits = sum(1 for kw in ALL_KEYWORDS if kw in text_lower)

    # On plafonne à 5 hits avancés et 10 hits totaux
    score = min(advanced_hits / 5, 1.0) * 15 + min(total_hits / 10, 1.0) * 10
    return round(score, 2)


def _view_score(view_count: int, age_days: float) -> float:
    """Vues pondérées par ancienneté (0-25)."""
    if age_days <= 0:
        age_days = 1
    # Vues par jour, log-normalisé
    vpd = view_count / age_days
    # Référence : 1000 vues/jour = score max
    score = min(math.log1p(vpd) / math.log1p(1000), 1.0) * 25
    return round(score, 2)


def _like_ratio_score(like_count: int, view_count: int) -> float:
    """Ratio likes/vues (0-20). Référence : 5% = max."""
    if view_count == 0:
        return 0.0
    ratio = like_count / view_count
    score = min(ratio / 0.05, 1.0) * 20
    return round(score, 2)


def _duration_score(duration_seconds: int) -> float:
    """10 pts si durée >= 10 min, sinon 0."""
    return 10.0 if duration_seconds >= 600 else 0.0


def _chapters_score(has_chapters: bool) -> float:
    """10 pts si la vidéo a des chapitres."""
    return 10.0 if has_chapters else 0.0


def _topics_score(topics: list[str]) -> float:
    """10 pts selon le nb de topics distincts (max 3)."""
    return round(min(len(topics) / 3, 1.0) * 10, 2)


def score_video(video_data: dict) -> Tuple[float, List[str]]:
    """
    Calcule le score d'une vidéo et retourne (score, topics).
    video_data doit contenir les clés du modèle Video.
    """
    now = datetime.now(timezone.utc)
    published_at = video_data["published_at"]
    if isinstance(published_at, str):
        from datetime import datetime as dt
        published_at = dt.fromisoformat(published_at.replace("Z", "+00:00"))

    age_days = (now - published_at).total_seconds() / 86400

    # Texte analysable : titre + tags
    tags_text = " ".join(video_data.get("tags", []))
    full_text = f"{video_data['title']} {tags_text}"

    topics = _detect_topics(full_text)

    raw = (
        _view_score(video_data["view_count"], age_days)
        + _like_ratio_score(video_data["like_count"], video_data["view_count"])
        + _keyword_score(full_text)
        + _duration_score(video_data["duration_seconds"])
        + _chapters_score(video_data.get("has_chapters", False))
        + _topics_score(topics)
    )

    # Normaliser sur 100 (max théorique = 25+20+25+10+10+10 = 100)
    final_score = round(min(raw, 100.0), 1)
    return final_score, topics
