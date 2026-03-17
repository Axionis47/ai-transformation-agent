"use client";

import { useState, useEffect } from "react";

const SECTIONS = [
  { id: "section-exec-summary",   label: "Executive Summary" },
  { id: "section-current-state",  label: "Current State" },
  { id: "section-use-cases",      label: "Use Cases" },
  { id: "section-roi",            label: "ROI Analysis" },
  { id: "section-roadmap",        label: "Roadmap" },
];

export default function ReportNav() {
  const [active, setActive] = useState<string>(SECTIONS[0].id);

  // Highlight the section nearest to viewport top as user scrolls
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
      className="neo-flat px-3 py-2 flex flex-wrap items-center gap-1"
      aria-label="Report sections"
    >
      <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 pr-2 border-r border-gray-200 mr-1">
        Jump to
      </span>
      {SECTIONS.map(({ id, label }) => {
        const isActive = active === id;
        return (
          <button
            key={id}
            onClick={() => scrollTo(id)}
            className="text-xs font-medium px-3 py-1.5 rounded-lg transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5]"
            style={
              isActive
                ? {
                    background: "#4f6df5",
                    color: "#fff",
                    boxShadow: "2px 2px 6px rgba(79,109,245,0.35), -1px -1px 4px rgba(255,255,255,0.6)",
                  }
                : {
                    background: "transparent",
                    color: "#6b7280",
                  }
            }
          >
            {label}
          </button>
        );
      })}
    </nav>
  );
}
