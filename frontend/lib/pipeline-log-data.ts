// Re-exports from config.ts — kept for backward compatibility.
// Import directly from "@/lib/config" in new code.
export type { FakeEntry } from "@/lib/config";
export { FAKE_LOG_ENTRIES as FAKE_ENTRIES, AGENT_COLORS } from "@/lib/config";

export function fmtTime(secs: number): string {
  const m = Math.floor(secs / 60).toString().padStart(2, "0");
  const s = (secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}
