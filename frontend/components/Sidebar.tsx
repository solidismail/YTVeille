"use client";

export default function Sidebar() {
    const navItems = [
        { icon: "▶", label: "Veille", id: "feed", badge: null, active: true },
        { icon: "🔍", label: "Explorer", id: "explore", badge: null, active: false },
        { icon: "⭐", label: "Favoris", id: "favorites", badge: null, active: false },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar__logo">
                <div className="sidebar__logo-icon">☸</div>
                <span>K8s Veille</span>
            </div>

            <nav className="sidebar__nav">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        id={`nav-${item.id}`}
                        className={`sidebar__nav-item${item.active ? " sidebar__nav-item--active" : ""}`}
                    >
                        <span>{item.icon}</span>
                        <span>{item.label}</span>
                        {item.badge && <span className="sidebar__badge">{item.badge}</span>}
                    </button>
                ))}

                <p className="sidebar__section-title">Topics</p>
                {["🔥 Incident", "🏗️ Architecture", "📊 Observabilité", "⚙️ CI/CD", "📈 Scaling"].map((t) => (
                    <button key={t} className="sidebar__nav-item" style={{ fontSize: "13px" }}>
                        {t}
                    </button>
                ))}
            </nav>

            <div className="sidebar__footer">
                <button className="sidebar__nav-item" style={{ width: "100%", borderRadius: 8 }}>
                    ⚙️ Paramètres
                </button>
            </div>
        </aside>
    );
}
