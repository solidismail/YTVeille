const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Video {
    id: string;
    title: string;
    channel: string;
    published_at: string;
    duration_seconds: number;
    view_count: number;
    like_count: number;
    thumbnail_url: string;
    youtube_url: string;
    tags: string[];
    has_chapters: boolean;
    score: number;
    topics: string[];
}

export interface VideoList {
    total: number;
    page: number;
    page_size: number;
    items: Video[];
}

export interface Filters {
    q?: string;
    min_score?: number;
    topic?: string;
    days?: number;
    page?: number;
    page_size?: number;
}

export async function fetchVideos(filters: Filters = {}): Promise<VideoList> {
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.min_score !== undefined) params.set("min_score", String(filters.min_score));
    if (filters.topic) params.set("topic", filters.topic);
    if (filters.days) params.set("days", String(filters.days));
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));

    const res = await fetch(`${API_BASE}/api/videos?${params}`, { next: { revalidate: 300 } });
    if (!res.ok) throw new Error("Erreur lors du chargement des vidéos");
    return res.json();
}

export async function triggerRefresh(queries?: string[]): Promise<void> {
    const body = queries ? JSON.stringify({ queries }) : undefined;
    await fetch(`${API_BASE}/api/refresh`, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : {},
        body,
    });
}

export async function fetchConfig(): Promise<{ queries: string[] }> {
    const res = await fetch(`${API_BASE}/api/config`, { cache: "no-store" });
    if (!res.ok) throw new Error("Erreur config");
    return res.json();
}

export async function fetchStatus(): Promise<{ video_count: number; last_updated: string | null; refresh_running: boolean; quota_exceeded: boolean; quota_exceeded_at: string | null }> {
    const res = await fetch(`${API_BASE}/api/status`, { cache: "no-store" });
    if (!res.ok) throw new Error("Erreur status");
    return res.json();
}

export function formatDuration(seconds: number): string {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h${String(m).padStart(2, "0")}`;
    return `${m}:${String(s).padStart(2, "0")}`;
}

export function formatDate(iso: string): string {
    return new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export const TOPICS: Record<string, string> = {
    incident: "🔥 Incident",
    architecture: "🏗️ Architecture",
    "observabilité": "📊 Observabilité",
    "sécurité": "🔒 Sécurité",
    ci_cd: "⚙️ CI/CD",
    scaling: "📈 Scaling",
    migration: "🔄 Migration",
    storage: "💾 Storage",
};
