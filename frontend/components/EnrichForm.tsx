"use client";

import { useState } from "react";
import type { Hypothesis, EnrichmentInput, EnrichmentCategory } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import { ENRICHMENT_CATEGORIES as CATEGORIES } from "@/config/constants";

interface Props {
  hypotheses: Hypothesis[];
  onSubmit: (inputs: EnrichmentInput[]) => void;
  loading: boolean;
}

export default function EnrichForm({ hypotheses, onSubmit, loading }: Props) {
  const [items, setItems] = useState<EnrichmentInput[]>([]);
  const [category, setCategory] = useState<EnrichmentCategory>("technology");
  const [title, setTitle] = useState("");
  const [detail, setDetail] = useState("");
  const [targetIds, setTargetIds] = useState<string[]>([]);

  function addItem() {
    if (!title.trim() || !detail.trim()) return;
    setItems([
      ...items,
      {
        category,
        title: title.trim(),
        detail: detail.trim(),
        affected_hypothesis_ids: targetIds,
        confidence: 0.9,
      },
    ]);
    setTitle("");
    setDetail("");
    setTargetIds([]);
  }

  function removeItem(idx: number) {
    setItems(items.filter((_, i) => i !== idx));
  }

  function toggleHypothesis(hid: string) {
    setTargetIds((prev) => (prev.includes(hid) ? prev.filter((id) => id !== hid) : [...prev, hid]));
  }

  const catVariant: Record<string, "mint" | "amber" | "rose" | "indigo" | "muted"> = {
    technology: "indigo",
    financials: "mint",
    operations: "amber",
    pain_points: "rose",
    constraints: "rose",
    corrections: "rose",
    additional_context: "muted",
  };

  return (
    <div className="space-y-6">
      {/* Input form */}
      <div className="bg-canvas-raised border border-edge-subtle rounded-md p-5 space-y-4">
        <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">
          Add Observation
        </p>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-2xs text-ink-secondary uppercase tracking-wider mb-1.5 block font-medium">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as EnrichmentCategory)}
              className="w-full bg-canvas-inset border border-edge text-ink text-sm p-2.5 rounded focus:border-mint focus:outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div className="col-span-2">
            <label className="text-2xs text-ink-secondary uppercase tracking-wider mb-1.5 block font-medium">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. ERP system is SAP S/4"
              className="w-full bg-canvas-inset border border-edge text-ink text-sm p-2.5 rounded focus:border-mint focus:outline-none"
            />
          </div>
        </div>
        <div>
          <label className="text-2xs text-ink-secondary uppercase tracking-wider mb-1.5 block font-medium">
            Detail
          </label>
          <textarea
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            rows={3}
            placeholder="What did you learn? Be specific — costs, systems, team feedback..."
            className="w-full bg-canvas-inset border border-edge text-ink text-sm p-2.5 rounded focus:border-mint focus:outline-none resize-none leading-relaxed"
          />
        </div>

        {/* Hypothesis targeting */}
        {hypotheses.length > 0 && (
          <div>
            <label className="text-2xs text-ink-secondary uppercase tracking-wider mb-2 block font-medium">
              Affects (optional)
            </label>
            <div className="space-y-1.5 max-h-32 overflow-y-auto">
              {hypotheses.map((h) => (
                <label
                  key={h.hypothesis_id}
                  className="flex items-start gap-2 cursor-pointer text-sm text-ink-secondary hover:text-ink"
                >
                  <input
                    type="checkbox"
                    checked={targetIds.includes(h.hypothesis_id)}
                    onChange={() => toggleHypothesis(h.hypothesis_id)}
                    className="mt-1 accent-mint"
                  />
                  <span className="line-clamp-1">{h.statement}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={addItem}
          disabled={!title.trim() || !detail.trim()}
          className="bg-canvas-overlay border border-edge text-ink text-sm px-4 py-2 rounded hover:border-mint transition-colors disabled:opacity-30"
        >
          + Add to Batch
        </button>
      </div>

      {/* Accumulated items */}
      {items.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">
            {items.length} item{items.length !== 1 ? "s" : ""} queued
          </p>
          {items.map((item, i) => (
            <div
              key={i}
              className="bg-canvas-raised border border-edge-subtle rounded-md p-3 flex items-start gap-3"
            >
              <Badge variant={catVariant[item.category] ?? "muted"}>
                {item.category.replace("_", " ")}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-ink">{item.title}</p>
                <p className="text-2xs text-ink-secondary line-clamp-1 mt-0.5">{item.detail}</p>
              </div>
              <button
                onClick={() => removeItem(i)}
                className="text-ink-tertiary hover:text-rose text-sm shrink-0"
              >
                &times;
              </button>
            </div>
          ))}
          <button
            onClick={() => onSubmit(items)}
            disabled={loading}
            className="w-full bg-mint text-ink-inverse py-3 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors mt-3"
          >
            {loading
              ? "Enriching Analysis..."
              : `Submit ${items.length} Observation${items.length !== 1 ? "s" : ""}`}
          </button>
        </div>
      )}
    </div>
  );
}
