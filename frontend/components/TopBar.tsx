"use client";

import { useState } from "react";
import { triggerRefresh } from "@/lib/api";

interface Props {
    lastUpdated: string | null;
    videoCount: number;
    onSearch: (q: string) => void;
    dark: boolean;
    onToggleDark: () => void;
}

export default function TopBar({ lastUpdated, videoCount, onSearch, dark, onToggleDark }: Props) {
    const [refreshing, setRefreshing] = useState(false);
    const [inputValue, setInputValue] = useState("");

    const commitSearch = () => onSearch(inputValue);

    const handleRefresh = async () => {
        commitSearch();
        setRefreshing(true);
        try {
            await triggerRefresh();
            setTimeout(() => window.location.reload(), 3000);
        } catch {
            // silently fail
        } finally {
            setTimeout(() => setRefreshing(false), 3000);
        }
    };

    return (
        <header className="topbar">
            <div className="topbar__search">
                <span>🔍</span>
                <input
                    id="search-input"
                    type="text"
                    placeholder="Rechercher dans les vidéos... (Entrée pour valider)"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && commitSearch()}
                />
            </div>

            {lastUpdated && (
                <p className="topbar__status">
                    {videoCount} vidéos · mis à jour {new Intl.RelativeTimeFormat("fr", { numeric: "auto" }).format(
                        -Math.round((Date.now() - new Date(lastUpdated).getTime()) / 3600000),
                        "hours"
                    )}
                </p>
            )}

            <button
                className="topbar__theme-btn"
                onClick={onToggleDark}
                title={dark ? "Passer en mode clair" : "Passer en mode sombre"}
                aria-label="Basculer le thème"
            >
                {dark ? "☀️" : "🌙"}
            </button>

            <button
                id="btn-refresh"
                className="topbar__btn"
                onClick={handleRefresh}
                disabled={refreshing}
            >
                {refreshing ? "⟳ Actualisation..." : "⟳ Actualiser"}
            </button>
        </header>
    );
}
