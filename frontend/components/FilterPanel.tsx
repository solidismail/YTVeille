"use client";

import { useState, useEffect } from "react";

interface FilterState {
    min_score: number;
    days: number;
}

interface Props {
    filters: FilterState;
    onChange: (f: Partial<FilterState>) => void;
    total: number;
    initialQueries: string[];
    onLaunch: (queries: string[]) => void;
    launching: boolean;
    activeQueryFilters: string[];
    onQueryFilterToggle: (q: string) => void;
}

const DAYS_OPTIONS = [7, 30, 90];

export default function FilterPanel({ filters, onChange, total, initialQueries, onLaunch, launching, activeQueryFilters, onQueryFilterToggle }: Props) {
    const [queries, setQueries] = useState<string[]>(initialQueries);
    const [inputValue, setInputValue] = useState("");

    useEffect(() => {
        setQueries(initialQueries);
    }, [initialQueries]);

    const addQuery = () => {
        const q = inputValue.trim();
        if (q && !queries.includes(q)) {
            setQueries([...queries, q]);
            setInputValue("");
        }
    };

    const removeQuery = (i: number) => {
        setQueries(queries.filter((_, idx) => idx !== i));
    };

    return (
        <aside className="filters">
            {/* Brand */}
            <div className="filters__brand">
                <div className="filters__brand-icon">▶</div>
                <span>YTVeille</span>
            </div>

            {/* Requêtes de recherche */}
            <div className="filters__group">
                <p className="filters__label">Requêtes de recherche</p>
                <div className="filters__queries">
                    {queries.map((q, i) => (
                        <div key={i} className="query-item">
                            <span className="query-item__text">{q}</span>
                            <button
                                className="query-item__remove"
                                onClick={() => removeQuery(i)}
                                title="Supprimer"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
                <div className="filters__add-query">
                    <input
                        type="text"
                        placeholder='Ex: "Docker production français"'
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && addQuery()}
                        className="filters__query-input"
                    />
                    <button className="filters__add-btn" onClick={addQuery} title="Ajouter">+</button>
                </div>
                <button
                    className="filters__launch"
                    onClick={() => onLaunch(queries)}
                    disabled={launching || queries.length === 0}
                >
                    {launching ? "⟳ Recherche en cours..." : "▶ Lancer la veille"}
                </button>
            </div>

            <div className="filters__divider" />

            {/* Filtrer par requête */}
            {queries.length > 0 && (
                <div className="filters__group">
                    <p className="filters__label">Filtrer par requête</p>
                    <div className="filters__chips">
                        {queries.map((q, i) => (
                            <button
                                key={i}
                                className={`chip${activeQueryFilters.includes(q) ? " chip--active" : ""}`}
                                onClick={() => onQueryFilterToggle(q)}
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Score minimum */}
            <div className="filters__group">
                <label className="filters__label" htmlFor="slider-score">Score minimum</label>
                <div className="filters__score-display">
                    <span>0</span>
                    <span style={{ color: "var(--primary)", fontWeight: 700 }}>{filters.min_score}</span>
                    <span>100</span>
                </div>
                <input
                    id="slider-score"
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={filters.min_score}
                    onChange={(e) => onChange({ min_score: Number(e.target.value) })}
                    className="filters__slider"
                />
            </div>

            {/* Période */}
            <div className="filters__group">
                <p className="filters__label">Période</p>
                <div className="filters__days">
                    {DAYS_OPTIONS.map((d) => (
                        <button
                            key={d}
                            id={`days-${d}`}
                            className={`day-btn${filters.days === d ? " day-btn--active" : ""}`}
                            onClick={() => onChange({ days: d })}
                        >
                            {d}j
                        </button>
                    ))}
                </div>
            </div>

            {/* Reset filtres */}
            <button
                id="btn-reset-filters"
                className="filters__reset"
                onClick={() => onChange({ min_score: 0, days: 30 })}
            >
                ↺ Réinitialiser les filtres
            </button>

            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: "auto" }}>
                {total} vidéo{total > 1 ? "s" : ""} trouvée{total > 1 ? "s" : ""}
            </p>
        </aside>
    );
}
