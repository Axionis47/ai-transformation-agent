"use client";

import { useState, useEffect } from "react";

const SECTIONS = [
  { id: "section-exec-summary",  label: "Executive Summary" },
  { id: "section-current-state", label: "Current State" },
  { id: "section-use-cases",     label: "Use Cases" },
  { id: "section-roi",           label: "ROI Analysis" },
  { id: "section-roadmap",       label: "Roadmap" },
];

export default function ReportNav() {
  const [active, setActive] = useState<string>(SECTIONS[0].id);

  useEffect(() => {
    function onScroll() {
      const offset = 120;
      for (let i = SECTIONS.length - 1; i >= 0; i--) {
        const el = document.getElementById(SECTIONS[i].id);
        if (el && el.getBoundingClientRect().top <= offset) {
          setActive(SECTIONS[i].id);
          return;
        }
      }
      setActive(SECTIONS[0].id);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (!el) return;
    const y = el.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: y, behavior: "smooth" });
    setActive(id);
  }

  return (
    <nav
      className="sticky top-0 z-10 bg-cream border-b border-rule flex flex-wrap items-stretch gap-0"
      aria-label="Report sections"
    >
      {SECTIONS.map(({ id, label }) => {
        const isActive = active === id;
        return (
          <button
            key={id}
            onClick={() => scrollTo(id)}
            className={[
              "font-label uppercase text-xs tracking-wider px-4 py-3 border-b-2 transition-colors duration-150 focus:outline-none",
              isActive
                ? "border-red text-ink"
                : "border-transparent text-ink-light hover:text-ink",
            ].join(" ")}
          >
            {label}
          </button>
        );
      })}
    </nav>
  );
}
