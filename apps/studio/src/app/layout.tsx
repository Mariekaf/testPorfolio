import type { Metadata } from "next";
import "./style.css";

export const metadata: Metadata = {
  title: "Portfolio Studio — Fondations",
  description: "Socle technique SaaS parallèle — CORE-001",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
