"use client";

import { useState } from "react";
import type { Assumption } from "@/lib/types";
import Badge from "@/components/ui/Badge";

interface AssumptionCardProps {
  assumption: Assumption;
  onUpdate?: (value: string) => void;
}

function confColor(c: number): "mint" | "amber" | "rose" {
  if (c >= 0.8) return "mint";
  if (c >= 0.5) return "amber";
  return "rose";
}

export default function AssumptionCard({ assumption, onUpdate }: AssumptionCardProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(assumption.value);

  function save() {
    setEditing(false);
    onUpdate?.(value);
  }

  return (
    <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">
          {assumption.field.replace(/_/g, " ")}
        </span>
        <div className="flex items-center gap-2">
          <Badge variant={confColor(assumption.confidence)}>
            {(assumption.confidence * 100).toFixed(0)}%
          </Badge>
          <Badge variant="muted">{assumption.source}</Badge>
        </div>
      </div>

      {editing ? (
        <div className="space-y-2">
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            rows={3}
            className="w-full bg-canvas-inset border border-edge text-ink text-sm font-sans p-3 rounded-md focus:border-mint focus:outline-none resize-none leading-relaxed"
          />
          <div className="flex gap-2">
            <button
              onClick={save}
              className="text-2xs font-medium text-mint hover:text-mint-bright transition-colors"
            >
              Save
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setValue(assumption.value);
              }}
              className="text-2xs font-medium text-ink-tertiary hover:text-ink-secondary transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="group">
          <p className="text-base text-ink leading-relaxed max-w-prose">{value}</p>
          {onUpdate && (
            <button
              onClick={() => setEditing(true)}
              className="mt-2 text-2xs font-medium text-ink-tertiary hover:text-mint transition-colors opacity-0 group-hover:opacity-100"
            >
              Edit
            </button>
          )}
        </div>
      )}
    </div>
  );
}
