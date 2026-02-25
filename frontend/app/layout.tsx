import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "YTVeille — Veille automatique YouTube en français",
    description:
        "Veille automatique des meilleures vidéos YouTube en français sur n'importe quel domaine technique.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr">
            <body>{children}</body>
        </html>
    );
}
