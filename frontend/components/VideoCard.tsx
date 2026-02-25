"use client";

import type { Video } from "@/lib/api";
import { formatDuration, formatDate, TOPICS } from "@/lib/api";
import Image from "next/image";

interface Props {
    video: Video;
}

export default function VideoCard({ video }: Props) {
    const scoreColor =
        video.score >= 70 ? "var(--primary)" : video.score >= 40 ? "#f59e0b" : "#6b7280";

    return (
        <a
            href={video.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="video-card"
            id={`video-${video.id}`}
            aria-label={`Voir la vidéo : ${video.title}`}
        >
            {/* Thumbnail */}
            <div className="video-card__thumb">
                {video.thumbnail_url ? (
                    <Image
                        src={video.thumbnail_url}
                        alt={video.title}
                        fill
                        style={{ objectFit: "cover" }}
                        unoptimized
                    />
                ) : (
                    <div style={{ background: "#e5e7eb", width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>☸</div>
                )}

                {/* Score badge */}
                <span className="video-card__score" style={{ background: scoreColor }}>
                    {video.score.toFixed(0)}/100
                </span>

                {/* Duration */}
                <span className="video-card__duration">{formatDuration(video.duration_seconds)}</span>

                {/* Chapters indicator */}
                {video.has_chapters && (
                    <span className="video-card__chapters">📑 Chapitres</span>
                )}
            </div>

            {/* Body */}
            <div className="video-card__body">
                <h3 className="video-card__title">{video.title}</h3>

                <div className="video-card__meta">
                    <span className="video-card__meta-item">📺 {video.channel}</span>
                    <span className="video-card__meta-item">📅 {formatDate(video.published_at)}</span>
                    <span className="video-card__meta-item">👁 {video.view_count.toLocaleString("fr-FR")}</span>
                    {video.like_count > 0 && (
                        <span className="video-card__meta-item">👍 {video.like_count.toLocaleString("fr-FR")}</span>
                    )}
                </div>

                {/* Topics */}
                {video.topics.length > 0 && (
                    <div className="video-card__topics">
                        {video.topics.slice(0, 3).map((t) => (
                            <span key={t} className="topic-tag">
                                {TOPICS[t] ?? t}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </a>
    );
}
