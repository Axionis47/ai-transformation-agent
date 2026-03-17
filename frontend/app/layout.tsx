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
      <body className="min-h-screen bg-neo-gradient flex flex-col">
        {/* Persistent header — home link anchor */}
        <header
          className="w-full border-b border-white/60 flex-shrink-0"
          style={{ background: "rgba(237,240,245,0.85)", backdropFilter: "blur(8px)" }}
        >
          <div className="max-w-2xl mx-auto px-6 py-3 flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5] rounded-lg"
            >
              <span
                className="inline-flex items-center justify-center w-7 h-7 rounded-neo-sm text-white text-xs font-bold"
                style={{ background: "linear-gradient(135deg, #5a76f6, #4463ef)" }}
              >
                AI
              </span>
              <span className="text-sm font-semibold" style={{ color: "#1e2433" }}>
                Discovery Agent
              </span>
            </Link>
            <span className="text-xs font-medium" style={{ color: "#718096" }}>
              Tenex Demo
            </span>
          </div>
        </header>

        <main className="max-w-2xl mx-auto w-full px-6 py-10 flex-1">
          {children}
        </main>

        {/* Footer */}
        <footer className="w-full flex-shrink-0 border-t border-white/40 mt-8">
          <div
            className="max-w-2xl mx-auto px-6 py-4 flex items-center justify-between"
            style={{ color: "#a0aec0" }}
          >
            <span className="text-xs">AI Transformation Discovery Agent</span>
            <span className="text-xs">v1.0 &middot; Tenex Demo</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
