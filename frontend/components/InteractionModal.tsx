"use client";

import { useState } from "react";
import Badge from "@/components/ui/Badge";
import type { UserInteractionPoint } from "@/lib/types";

interface InteractionModalProps {
  interaction: UserInteractionPoint;
  onRespond: (response: string) => void;
  onDismiss: () => void;
}

const TYPE_VARIANT: Record<string, "mint" | "amber" | "rose"> = {
  interesting_finding: "mint",
  confirmation: "amber",
  ambiguity: "rose",
};

export default function InteractionModal({
  interaction,
  onRespond,
  onDismiss,
}: InteractionModalProps) {
  const [response, setResponse] = useState("");
  const variant = TYPE_VARIANT[interaction.interaction_type] ?? "mint";

  return (
    <div className="fixed inset-0 bg-canvas/80 backdrop-blur-sm z-40 flex justify-center">
      <div className="bg-canvas-raised border border-edge rounded-md max-w-lg w-full mx-auto mt-24 p-6 h-fit">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm">⚡</span>
          <span className="text-xs font-semibold tracking-wider text-ink uppercase">Finding</span>
        </div>

        <p className="text-sm text-ink leading-relaxed mb-4">{interaction.message}</p>

        <div className="flex items-center gap-3 mb-4">
          <span className="text-2xs font-mono text-ink-tertiary">
            From: {interaction.agent_source}
          </span>
          <Badge variant={variant}>{interaction.interaction_type.replace(/_/g, " ")}</Badge>
        </div>

        <textarea
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="Your response (optional)..."
          rows={3}
          className="w-full bg-canvas-inset border border-edge rounded-md px-3 py-2 text-sm text-ink placeholder:text-ink-tertiary resize-none focus:outline-none focus:border-mint/50 font-mono"
        />

        <div className="flex items-center justify-between mt-4">
          <button
            onClick={onDismiss}
            className="text-ink-tertiary text-sm hover:text-ink transition-colors"
          >
            Dismiss
          </button>
          <button
            onClick={() => onRespond(response)}
            className="bg-mint text-ink-inverse text-sm font-medium px-4 py-1.5 rounded-md hover:bg-mint-bright transition-colors"
          >
            Respond
          </button>
        </div>
      </div>
    </div>
  );
}
