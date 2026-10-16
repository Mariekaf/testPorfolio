import type { Metadata } from "next";
import "./style.css";

export const metadata: Metadata = {
  title: "Portfolio Studio",
  description: "Votre espace personnel de création",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
