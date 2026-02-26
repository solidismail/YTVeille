"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import TopBar from "@/components/TopBar";
import VideoCard from "@/components/VideoCard";
import FilterPanel from "@/components/FilterPanel";
import { fetchVideos, fetchStatus, fetchConfig, triggerRefresh, type Video, type Filters } from "@/lib/api";

interface FilterState {
    min_score: number;
    days: number;
}

const DEFAULT_FILTERS: FilterState = { min_score: 0, days: 30 };
const PAGE_SIZE = 18;

export default function HomePage() {
    const [videos, setVideos] = useState<Video[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [initialQueries, setInitialQueries] = useState<string[]>([]);
    const [launching, setLaunching] = useState(false);
    const [activeQueryFilters, setActiveQueryFilters] = useState<string[]>([]);
    const [dark, setDark] = useState(false);

    // Lire la préférence stockée au montage
    useEffect(() => {
        const stored = localStorage.getItem("theme");
        const isDark = stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
        setDark(isDark);
        document.documentElement.classList.toggle("dark", isDark);
    }, []);

    const handleToggleDark = () => {
        setDark((prev) => {
            const next = !prev;
            document.documentElement.classList.toggle("dark", next);
            localStorage.setItem("theme", next ? "dark" : "light");
            return next;
        });
    };

    const [status, setStatus] = useState<{ video_count: number; last_updated: string | null; refresh_running: boolean; quota_exceeded: boolean; quota_exceeded_at: string | null }>({
        video_count: 0,
        last_updated: null,
        refresh_running: false,
        quota_exceeded: false,
        quota_exceeded_at: null,
    });
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const loadVideos = useCallback(async (f: FilterState, p: number, q: string) => {
        setLoading(true);
        try {
            const params: Filters = {
                q: q || undefined,
                min_score: f.min_score,
                days: f.days,
                page: p,
                page_size: PAGE_SIZE,
            };
            const result = await fetchVideos(params);
            setVideos(result.items);
            setTotal(result.total);
        } catch {
            setVideos([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // Charger config + statut au montage
    useEffect(() => {
        fetchConfig().then((c) => setInitialQueries(c.queries)).catch(() => {});
        fetchStatus().then(setStatus).catch(() => {});
    }, []);

    // Debounce de la recherche texte (300 ms)
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
            setPage(1);
        }, 300);
        return () => clearTimeout(timer);
    }, [search]);

    // Charger vidéos à chaque changement de filtres / page / recherche
    useEffect(() => {
        loadVideos(filters, page, debouncedSearch);
    }, [filters, page, debouncedSearch, loadVideos]);

    const handleFilterChange = (partial: Partial<FilterState>) => {
        setFilters((prev) => ({ ...prev, ...partial }));
        setPage(1);
    };

    const handleQueryFilterToggle = (q: string) => {
        setActiveQueryFilters((prev) =>
            prev.includes(q) ? prev.filter((x) => x !== q) : [...prev, q]
        );
    };

    const handleLaunch = async (queries: string[]) => {
        setLaunching(true);
        try {
            await triggerRefresh(queries);
            // Polling jusqu'à la fin du refresh
            pollRef.current = setInterval(async () => {
                try {
                    const s = await fetchStatus();
                    setStatus(s);
                    if (!s.refresh_running) {
                        clearInterval(pollRef.current!);
                        pollRef.current = null;
                        setLaunching(false);
                        setPage(1);
                        loadVideos(filters, 1, debouncedSearch);
                    }
                } catch {
                    clearInterval(pollRef.current!);
                    pollRef.current = null;
                    setLaunching(false);
                }
            }, 2000);
        } catch {
            setLaunching(false);
        }
    };

    // Nettoyage du polling au démontage
    useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

    const totalPages = Math.ceil(total / PAGE_SIZE);

    // Le filtre texte est géré côté backend (paramètre q).
    // Les chips de requête restent filtrées côté client sur la page courante.
    const displayedVideos = activeQueryFilters.length > 0
        ? videos.filter((v) =>
              activeQueryFilters.some((aq) =>
                  v.title.toLowerCase().includes(aq.toLowerCase())
              )
          )
        : videos;

    return (
        <div className="app-shell">
            <TopBar
                lastUpdated={status.last_updated}
                videoCount={status.video_count}
                onSearch={setSearch}
                dark={dark}
                onToggleDark={handleToggleDark}
            />

            <main className="main">
                <div className="main__header">
                    <h1 className="main__title">▶ YTVeille</h1>
                    <span className="main__count">{displayedVideos.length} vidéo{displayedVideos.length > 1 ? "s" : ""}</span>
                </div>

                {launching && (
                    <div className="main__launching">
                        <span>⟳ Recherche YouTube en cours, veuillez patienter...</span>
                    </div>
                )}

                {status.quota_exceeded && !launching && (
                    <div className="main__quota-banner">
                        <span className="main__quota-icon">⚠️</span>
                        <div>
                            <strong>Quota YouTube API dépassé</strong>
                            {status.quota_exceeded_at && (
                                <> — depuis le {new Intl.DateTimeFormat("fr-FR", {
                                    day: "numeric", month: "short",
                                    hour: "2-digit", minute: "2-digit",
                                }).format(new Date(status.quota_exceeded_at))}</>
                            )}
                            <br />
                            <span>Le quota se renouvelle chaque jour à minuit (heure du Pacifique, ~8h–9h UTC). Réessayez demain.</span>
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="main__grid">
                        {Array.from({ length: 6 }).map((_, i) => (
                            <div key={i} className="skeleton skeleton-card" />
                        ))}
                    </div>
                ) : displayedVideos.length === 0 ? (
                    <div className="main__empty">
                        <p style={{ fontSize: 40, marginBottom: 12 }}>▶</p>
                        <p>Aucune vidéo trouvée.</p>
                        <p style={{ marginTop: 8, fontSize: 13 }}>
                            Configurez vos requêtes et lancez la veille depuis le panneau gauche.
                        </p>
                    </div>
                ) : (
                    <div className="main__grid">
                        {displayedVideos.map((v) => (
                            <VideoCard key={v.id} video={v} />
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <nav className="pagination" aria-label="Pagination">
                        <button
                            id="btn-prev-page"
                            className="page-btn"
                            disabled={page === 1}
                            onClick={() => setPage((p) => p - 1)}
                        >
                            ← Précédent
                        </button>

                        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                            const p = i + 1;
                            return (
                                <button
                                    key={p}
                                    id={`btn-page-${p}`}
                                    className={`page-btn${page === p ? " page-btn--active" : ""}`}
                                    onClick={() => setPage(p)}
                                >
                                    {p}
                                </button>
                            );
                        })}

                        <button
                            id="btn-next-page"
                            className="page-btn"
                            disabled={page === totalPages}
                            onClick={() => setPage((p) => p + 1)}
                        >
                            Suivant →
                        </button>
                    </nav>
                )}
            </main>

            <FilterPanel
                filters={filters}
                onChange={handleFilterChange}
                total={total}
                initialQueries={initialQueries}
                onLaunch={handleLaunch}
                launching={launching}
                activeQueryFilters={activeQueryFilters}
                onQueryFilterToggle={handleQueryFilterToggle}
            />
        </div>
    );
}
