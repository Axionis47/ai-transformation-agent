import { FILTERS } from "@/config/constants";

export type Filter = (typeof FILTERS)[number];

interface TraceFilterBarProps {
  filter: Filter;
  onFilterChange: (f: Filter) => void;
}

export default function TraceFilterBar({ filter, onFilterChange }: TraceFilterBarProps) {
  return (
    <div className="flex gap-2 mb-6">
      {FILTERS.map((f) => (
        <button
          key={f}
          onClick={() => onFilterChange(f)}
          className={`text-2xs font-mono px-3 py-1.5 rounded transition-colors ${filter === f ? "bg-canvas-overlay text-ink border border-edge" : "text-ink-tertiary hover:text-ink-secondary"}`}
        >
          {f.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
