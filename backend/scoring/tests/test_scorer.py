"""Tests du scorer Kubernetes."""

import pytest
from datetime import datetime, timezone, timedelta
from scoring.scorer import score_video, _detect_topics, _keyword_score


def _base_video(**kwargs) -> dict:
    defaults = {
        "id": "test123",
        "title": "Kubernetes en production",
        "channel": "DevOps France",
        "published_at": datetime.now(timezone.utc) - timedelta(days=5),
        "duration_seconds": 1800,  # 30 min
        "view_count": 5000,
        "like_count": 250,
        "thumbnail_url": "https://example.com/thumb.jpg",
        "youtube_url": "https://youtube.com/watch?v=test123",
        "tags": ["kubernetes", "production", "devops"],
        "has_chapters": True,
    }
    defaults.update(kwargs)
    return defaults


class TestScoreVideo:
    def test_score_is_between_0_and_100(self):
        v = _base_video()
        score, topics = score_video(v)
        assert 0 <= score <= 100

    def test_long_video_scores_higher_than_short(self):
        long_v = _base_video(duration_seconds=1800)
        short_v = _base_video(duration_seconds=300)
        score_long, _ = score_video(long_v)
        score_short, _ = score_video(short_v)
        assert score_long > score_short

    def test_chapters_increase_score(self):
        with_ch = _base_video(has_chapters=True)
        without_ch = _base_video(has_chapters=False)
        s_with, _ = score_video(with_ch)
        s_without, _ = score_video(without_ch)
        assert s_with > s_without

    def test_advanced_keywords_increase_score(self):
        basic = _base_video(title="Kubernetes débutant", tags=[])
        advanced = _base_video(
            title="Kubernetes post-mortem ArgoCD Prometheus",
            tags=["istio", "hpa", "keda"],
        )
        s_basic, _ = score_video(basic)
        s_advanced, _ = score_video(advanced)
        assert s_advanced > s_basic

    def test_topics_detected(self):
        v = _base_video(title="Kubernetes ArgoCD CI/CD pipeline GitOps", tags=["argocd", "fluxcd"])
        _, topics = score_video(v)
        assert "ci_cd" in topics

    def test_incident_topic_detected(self):
        v = _base_video(title="Kubernetes post-mortem incident production outage")
        _, topics = score_video(v)
        assert "incident" in topics

    def test_zero_views_handled(self):
        v = _base_video(view_count=0, like_count=0)
        score, _ = score_video(v)
        assert score >= 0


class TestDetectTopics:
    def test_returns_list(self):
        topics = _detect_topics("Kubernetes monitoring Prometheus")
        assert isinstance(topics, list)

    def test_empty_text(self):
        topics = _detect_topics("")
        assert topics == []


class TestKeywordScore:
    def test_no_keywords(self):
        s = _keyword_score("bonjour le monde")
        assert s == 0.0

    def test_advanced_keyword(self):
        s = _keyword_score("post-mortem kubernetes production")
        assert s > 0
