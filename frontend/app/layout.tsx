import type { Metadata } from "next";
import {
  Playfair_Display,
  Libre_Baskerville,
  IBM_Plex_Mono,
  Barlow_Condensed,
} from "next/font/google";
import Link from "next/link";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "900"],
  variable: "--font-headline",
  display: "swap",
});

const baskerville = Libre_Baskerville({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-body",
  display: "swap",
});

const ibmMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-mono",
  display: "swap",
});

const barlow = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-label",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Transformation Discovery Agent",
  description: "AI maturity assessment and transformation roadmap generator",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const fontVariables = [
    playfair.variable,
    baskerville.variable,
    ibmMono.variable,
    barlow.variable,
  ].join(" ");

  return (
    <html lang="en" className={fontVariables}>
      <body className="bg-cream text-ink font-body antialiased min-h-screen flex flex-col">

        {/* 3px red masthead rule — very top of page */}
        <div className="rule-masthead" />

        {/* Navigation */}
        <header className="w-full">
          <div
            className="mx-auto flex items-center justify-between py-3"
            style={{ maxWidth: "920px", padding: "0.75rem clamp(1.5rem, 5vw, 4rem)" }}
          >
            <span className="font-label font-semibold uppercase tracking-widest text-sm text-ink">
              DISCOVERY AGENT
            </span>
            <nav className="flex items-center gap-5">
              <Link
                href="/solutions"
                className="font-label font-semibold uppercase tracking-wider text-xs text-ink-medium hover:text-red transition-colors"
              >
                Solutions
              </Link>
              <span className="font-label font-semibold uppercase tracking-wider text-xs text-ink-medium">
                Tenex Demo
              </span>
              <span className="font-mono text-xs text-ink-light">
                19 Mar 2026
              </span>
            </nav>
          </div>

          {/* 1px ink rule under nav */}
          <div className="rule-ink" />
          {/* 0.5px hairline sub-rule */}
          <div className="rule-hairline mt-px" />
        </header>

        {/* Main content */}
        <main
          className="mx-auto w-full flex-1"
          style={{ maxWidth: "920px", padding: "2.5rem clamp(1.5rem, 5vw, 4rem)" }}
        >
          {children}
        </main>

        {/* Footer */}
        <footer className="w-full">
          <div className="rule-hairline" />
          <div
            className="mx-auto flex items-center justify-between py-4"
            style={{ maxWidth: "920px", padding: "1rem clamp(1.5rem, 5vw, 4rem)" }}
          >
            <span className="font-mono text-xs text-ink-light">
              Built for Tenex — AI transformation for the mid-market
            </span>
            <span className="font-mono text-xs text-ink-faint">
              Multi-agent showcase
            </span>
          </div>
        </footer>

      </body>
    </html>
  );
}
