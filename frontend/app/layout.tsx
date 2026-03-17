import type { Metadata } from "next";
import { Inter } from "next/font/google";
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
      <body className="min-h-screen" style={{ background: "#e8ecf1" }}>
        <main className="max-w-2xl mx-auto px-6 py-12">{children}</main>
      </body>
    </html>
  );
}
