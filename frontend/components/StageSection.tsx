"use client";

import { useState } from "react";

type StageStatus = "active" | "completed" | "pending";

interface StageSectionProps {
  title: string;
  stageNumber: number;
  status: StageStatus;
  children?: React.ReactNode;
  summary?: string;
}

const STATUS_COLORS: Record<StageStatus, string> = {
  active: "text-accent",
  completed: "text-text-muted",
  pending: "text-border",
};

export default function StageSection({
  title,
  stageNumber,
  status,
  children,
  summary,
}: StageSectionProps) {
  const [expanded, setExpanded] = useState(status !== "completed");

  const statusLabel = status.toUpperCase();
  const statusColor = STATUS_COLORS[status];
  const isToggleable = status === "completed";

  return (
    <div className="border-b border-border last:border-0">
      <div
        className={`flex items-center gap-2 py-3 px-0 ${isToggleable ? "cursor-pointer" : ""}`}
        onClick={isToggleable ? () => setExpanded(!expanded) : undefined}
      >
        <span
          className="text-text-muted font-sans uppercase tracking-wider flex-shrink-0"
          style={{ fontSize: "14px", fontWeight: 600 }}
        >
          STAGE {stageNumber}: {title}
        </span>
        <div className="flex-1 border-t border-border" />
        <span
          className={`font-sans uppercase tracking-wider flex-shrink-0 ${statusColor}`}
          style={{ fontSize: "14px", fontWeight: 600 }}
        >
          {statusLabel}
        </span>
      </div>

      {status === "completed" && !expanded && summary && (
        <p className="text-text-muted pb-3" style={{ fontSize: "12px" }}>
          {summary}
        </p>
      )}

      {(status === "active" || (status === "completed" && expanded)) && (
        <div className="pb-4">{children}</div>
      )}
    </div>
  );
}
