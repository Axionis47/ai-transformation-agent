export interface FakeEntry {
  at: number;
  agent: string;
  message: string;
  done?: boolean;
}

export const FAKE_ENTRIES: FakeEntry[] = [
  { at: 0,  agent: "SCRAPE", message: "Fetching company pages..." },
  { at: 6,  agent: "SCRAPE", message: "Extracting page content..." },
  { at: 12, agent: "SCRAPE", message: "✓ Scrape complete", done: true },
  { at: 14, agent: "ANLYZ",  message: "Analyzing signals from content..." },
  { at: 22, agent: "ANLYZ",  message: "Classifying signal dimensions..." },
  { at: 30, agent: "ANLYZ",  message: "✓ Signal extraction complete", done: true },
  { at: 32, agent: "SCORE",  message: "Scoring AI maturity dimensions..." },
  { at: 40, agent: "SCORE",  message: "Computing composite score..." },
  { at: 47, agent: "SCORE",  message: "✓ Maturity scoring complete", done: true },
  { at: 49, agent: "REPRT",  message: "Querying victory library..." },
  { at: 57, agent: "REPRT",  message: "Generating use cases..." },
  { at: 65, agent: "REPRT",  message: "Writing report sections..." },
  { at: 75, agent: "REPRT",  message: "✓ Report generation complete", done: true },
];

export const AGENT_COLORS: Record<string, string> = {
  SCRAPE: "#1a1714",
  ANLYZ:  "#6b5b4f",
  SCORE:  "#c1272d",
  REPRT:  "#2d6a4f",
};

export function fmtTime(secs: number): string {
  const m = Math.floor(secs / 60).toString().padStart(2, "0");
  const s = (secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}
