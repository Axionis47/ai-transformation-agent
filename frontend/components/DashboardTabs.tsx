"use client";

export type TabId = "brief" | "report" | "evidence";

interface Tab {
  id: TabId;
  label: string;
}

const TABS: Tab[] = [
  { id: "brief", label: "Pitch Brief" },
  { id: "report", label: "Full Report" },
  { id: "evidence", label: "Evidence" },
];

interface DashboardTabsProps {
  activeTab: TabId;
  onTabChange: (id: TabId) => void;
}

export default function DashboardTabs({ activeTab, onTabChange }: DashboardTabsProps) {
  return (
    <div
      className="flex gap-0 border-b"
      style={{ borderColor: "var(--rule)" }}
      role="tablist"
      aria-label="Dashboard sections"
    >
      {TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className="font-label uppercase tracking-[0.1em] text-xs px-4 py-3 transition-colors relative"
            style={{
              color: isActive ? "var(--ink)" : "var(--ink-light)",
              fontWeight: isActive ? 700 : 400,
              borderBottom: isActive ? "2px solid var(--red)" : "2px solid transparent",
              marginBottom: "-1px",
              background: "transparent",
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
