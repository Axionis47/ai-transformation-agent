"use client";

import { useEffect, useState, useRef } from "react";
import { FAKE_ENTRIES, AGENT_COLORS, fmtTime } from "@/lib/pipeline-log-data";

interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
  done?: boolean;
}

interface PipelineProgressProps {
  onCancel?: () => void;
  isComplete?: boolean;
}

export default function PipelineProgress({ onCancel, isComplete }: PipelineProgressProps) {
  const [elapsed, setElapsed] = useState(0);
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const startRef = useRef(Date.now());
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (isComplete) {
      const now = Math.floor((Date.now() - startRef.current) / 1000);
      setEntries(FAKE_ENTRIES.map((e) => ({
        timestamp: fmtTime(e.at <= now ? e.at : now),
        agent: e.agent,
        message: e.message,
        done: e.done,
      })));
      return;
    }
    const timers = FAKE_ENTRIES.map((e) =>
      setTimeout(() => {
        setEntries((prev) => {
          if (prev.some((p) => p.agent === e.agent && p.message === e.message)) return prev;
          return [...prev, { timestamp: fmtTime(e.at), agent: e.agent, message: e.message, done: e.done }];
        });
      }, e.at * 1000)
    );
    return () => timers.forEach(clearTimeout);
  }, [isComplete]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [entries]);

  return (
    <div style={{ borderTop: "2px solid var(--ink)" }}>
      <div className="flex items-center gap-3 py-3">
        <span className="w-2 h-2 rounded-full flex-shrink-0 animate-pulse" style={{ background: "var(--red)" }} />
        <span className="font-label font-bold uppercase tracking-widest text-sm text-ink flex-1">
          PIPELINE EXECUTION
        </span>
        <span className="font-mono text-xs text-ink-light mr-4">{fmtTime(elapsed)}</span>
        {onCancel && (
          <button
            onClick={onCancel}
            className="font-label uppercase text-xs border border-ink bg-cream text-ink px-3 py-1 transition-colors hover:bg-red hover:text-cream hover:border-red"
          >
            Cancel
          </button>
        )}
      </div>
      <div className="rule-hairline" />
      <div ref={logRef} className="overflow-y-auto py-3" style={{ maxHeight: "340px" }}>
        {entries.length === 0 && (
          <span className="font-mono text-xs text-ink-faint">Initializing...</span>
        )}
        {entries.map((entry, i) => (
          <div
            key={i}
            className="grid font-mono text-xs py-0.5"
            style={{ gridTemplateColumns: "3.5rem 3.5rem 1fr", gap: "0.75rem", animation: "revealUp 0.25s ease forwards" }}
          >
            <span className="text-ink-light">{entry.timestamp}</span>
            <span className="font-semibold" style={{ color: AGENT_COLORS[entry.agent] ?? "#1a1714" }}>{entry.agent}</span>
            <span style={{ color: entry.done ? "var(--red)" : "var(--ink-medium)" }}>{entry.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
