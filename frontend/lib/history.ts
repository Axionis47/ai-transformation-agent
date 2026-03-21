import type { AnalyzeSuccess } from "@/lib/types";
import { API_BASE } from "@/lib/config";

export interface HistoryEntry {
  run_id: string;
  url: string;
  score: number;
  label: string;
  date: string; // ISO string
}

const STORAGE_KEY = "analysis_history";
const MAX_ENTRIES = 10;

function loadRaw(): { entries: HistoryEntry[]; full: Record<string, AnalyzeSuccess> } {
  if (typeof window === "undefined") return { entries: [], full: {} };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { entries: [], full: {} };
    return JSON.parse(raw) as { entries: HistoryEntry[]; full: Record<string, AnalyzeSuccess> };
  } catch {
    return { entries: [], full: {} };
  }
}

function persist(entries: HistoryEntry[], full: Record<string, AnalyzeSuccess>): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ entries, full }));
  } catch {
    // localStorage quota exceeded — ignore
  }
}

export function saveAnalysis(url: string, data: AnalyzeSuccess): void {
  const { entries, full } = loadRaw();

  const entry: HistoryEntry = {
    run_id: data.run_id,
    url,
    score: data.maturity.composite_score,
    label: data.maturity.composite_label,
    date: new Date().toISOString(),
  };

  // Remove existing entry with same run_id if present
  const filtered = entries.filter((e) => e.run_id !== data.run_id);
  const next = [entry, ...filtered].slice(0, MAX_ENTRIES);

  full[data.run_id] = data;

  // Prune full store to match kept entries
  const keptIds = new Set(next.map((e) => e.run_id));
  for (const id of Object.keys(full)) {
    if (!keptIds.has(id)) delete full[id];
  }

  persist(next, full);
}

export function getHistory(): HistoryEntry[] {
  return loadRaw().entries;
}

export function getAnalysis(run_id: string): AnalyzeSuccess | null {
  const { full } = loadRaw();
  return full[run_id] ?? null;
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

/**
 * Fetch run history from the backend (requires Firebase ID token).
 * Returns an empty array on any error — callers should fall back to
 * getHistory() (localStorage) when this returns nothing.
 */
export async function fetchRemoteHistory(token: string): Promise<HistoryEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/v1/runs`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    const data = await res.json() as { runs?: unknown[] };
    if (!Array.isArray(data.runs)) return [];
    return data.runs.map((r) => {
      const run = r as Record<string, unknown>;
      const readiness = run["readiness"] as Record<string, unknown> | undefined;
      const maturity = run["maturity"] as Record<string, unknown> | undefined;
      return {
        run_id: String(run["run_id"] ?? ""),
        url: String(run["url"] ?? ""),
        score: Number(readiness?.["score"] ?? maturity?.["composite_score"] ?? 0),
        label: String(readiness?.["label"] ?? maturity?.["composite_label"] ?? ""),
        date: String(run["created_at"] ?? new Date().toISOString()),
      };
    });
  } catch {
    return [];
  }
}
