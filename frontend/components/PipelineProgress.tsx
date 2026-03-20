"use client";

import { useEffect, useState, useRef } from "react";
import { FAKE_LOG_ENTRIES, AGENT_COLORS, LAYOUT, STRINGS } from "@/lib/config";
import { fmtTime } from "@/lib/pipeline-log-data";

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

  // Track whether all fake entries have been shown
  const [fakesDone, setFakesDone] = useState(false);

  useEffect(() => {
    if (isComplete) {
      // Show all fake entries + final completion line
      const now = Math.floor((Date.now() - startRef.current) / 1000);
      const all = FAKE_LOG_ENTRIES.map((e) => ({
        timestamp: fmtTime(e.at <= now ? e.at : now),
        agent: e.agent,
        message: e.message,
        done: e.done,
      }));
      all.push({ timestamp: fmtTime(now), agent: "REPRT", message: STRINGS.analysisComplete, done: true });
      setEntries(all);
      return;
    }
    const timers = FAKE_LOG_ENTRIES.map((e, i) =>
      setTimeout(() => {
        setEntries((prev) => {
          if (prev.some((p) => p.agent === e.agent && p.message === e.message)) return prev;
          return [...prev, { timestamp: fmtTime(e.at), agent: e.agent, message: e.message, done: e.done }];
        });
        if (i === FAKE_LOG_ENTRIES.length - 1) setFakesDone(true);
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
          {STRINGS.pipelineExecution}
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
      <div ref={logRef} className="overflow-y-auto py-3" style={{ maxHeight: `${LAYOUT.logMaxHeight}px` }}>
        {entries.length === 0 && (
          <span className="font-mono text-xs text-ink-faint">{STRINGS.initializing}</span>
        )}
        {entries.map((entry, i) => (
          <div
            key={i}
            className="grid font-mono text-xs py-0.5"
            style={{ gridTemplateColumns: "3.5rem 3.5rem 1fr", gap: "0.75rem", animation: "revealUp 0.25s ease forwards" }}
          >
            <span className="text-ink-light">{entry.timestamp}</span>
            <span className="font-semibold" style={{ color: AGENT_COLORS[entry.agent] ?? AGENT_COLORS.SCRAPE }}>{entry.agent}</span>
            <span style={{ color: entry.done ? "var(--red)" : "var(--ink-medium)" }}>{entry.message}</span>
          </div>
        ))}
        {fakesDone && !isComplete && (
          <div className="grid font-mono text-xs py-0.5 animate-pulse" style={{ gridTemplateColumns: "3.5rem 3.5rem 1fr", gap: "0.75rem" }}>
            <span className="text-ink-light">{fmtTime(elapsed)}</span>
            <span className="font-semibold text-ink-light">SYS</span>
            <span className="text-ink-faint">{STRINGS.waitingForResponse}</span>
          </div>
        )}
      </div>
    </div>
  );
}
