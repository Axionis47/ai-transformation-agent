"use client";

export default function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <div className="flex-1 border-t border-edge-subtle" />
      </div>
      {subtitle && <p className="text-sm text-ink-tertiary">{subtitle}</p>}
    </div>
  );
}
