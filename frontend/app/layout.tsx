import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
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
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-neo-gradient">
        {/* Persistent header bar */}
        <header className="w-full border-b border-white/60" style={{ background: "rgba(237,240,245,0.85)", backdropFilter: "blur(8px)" }}>
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className="inline-flex items-center justify-center w-7 h-7 rounded-neo-sm text-white text-xs font-bold"
                style={{ background: "linear-gradient(135deg, #5a76f6, #4463ef)" }}
              >
                AI
              </span>
              <span className="text-sm font-semibold" style={{ color: "#1e2433" }}>
                Discovery Agent
              </span>
            </div>
            <nav className="flex items-center gap-4">
              <Link
                href="/solutions"
                className="text-xs font-medium hover:underline transition-colors"
                style={{ color: "#4f6df5" }}
              >
                Solutions
              </Link>
              <span className="text-xs font-medium" style={{ color: "#718096" }}>
                Tenex Demo
              </span>
            </nav>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
