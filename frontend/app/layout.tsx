import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="en">
      <body className="min-h-screen" style={{ background: "#e0e5ec" }}>
        <header className="px-8 py-6 border-b border-neo-dark/20">
          <div className="max-w-5xl mx-auto">
            <h1 className="text-xl font-semibold text-gray-700 tracking-tight">
              AI Transformation Discovery
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Maturity assessment in 90 seconds
            </p>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-8 py-10">{children}</main>
      </body>
    </html>
  );
}
