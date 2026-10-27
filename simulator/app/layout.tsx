import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Simulátor obchodování",
  description: "Simulovaný broker s živými daty, botem a agenty, kteří rozhodují o každém obchodu.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#0f1117" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs">
      <body>{children}</body>
    </html>
  );
}
