import type { Meta, StoryObj } from "@storybook/react";
import TracePanel from "@/components/TracePanel";
import type { TraceStage } from "@/components/TraceStageRow";

const meta: Meta<typeof TracePanel> = {
  title: "Components/TracePanel",
  component: TracePanel,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof TracePanel>;

export const MOCK_STAGES: TraceStage[] = [
  {
    agent_tag: "SCRAPER",
    event: "agent_complete",
    latency_ms: 1240,
    prompt_file: null,
    prompt_version: null,
    input_summary: { url: "https://example.com" },
    output_summary: { pages_fetched: 3, total_chars: 4500 },
    timestamp: "2026-03-16T12:00:00Z",
  },
  {
    agent_tag: "SIGNAL_EXTRACTOR",
    event: "agent_complete",
    latency_ms: 2800,
    prompt_file: "signals.md",
    prompt_version: "1.2",
    input_summary: { chars: 4500, pages: 3 },
    output_summary: { signals_found: 12, confidence: "HIGH" },
    timestamp: "2026-03-16T12:00:01Z",
  },
  {
    agent_tag: "MATURITY_SCORER",
    event: "agent_complete",
    latency_ms: 3100,
    prompt_file: "consultant.md",
    prompt_version: "2.1",
    input_summary: { signals: 12, industry: "Logistics" },
    output_summary: { composite_score: 2.8, composite_label: "Developing" },
    timestamp: "2026-03-16T12:00:04Z",
  },
  {
    agent_tag: "RAG",
    event: "agent_complete",
    latency_ms: 340,
    prompt_file: null,
    prompt_version: null,
    input_summary: { query: "logistics AI maturity", top_k: 5 },
    output_summary: { matches_returned: 5, top_score: 0.91 },
    timestamp: "2026-03-16T12:00:07Z",
  },
  {
    agent_tag: "VICTORY_MATCHER",
    event: "agent_complete",
    latency_ms: 1950,
    prompt_file: "rag_query.md",
    prompt_version: "1.0",
    input_summary: { candidates: 5, maturity_label: "Developing" },
    output_summary: { direct_matches: 2, calibration_matches: 2 },
    timestamp: "2026-03-16T12:00:09Z",
  },
  {
    agent_tag: "USE_CASE_GENERATOR",
    event: "agent_complete",
    latency_ms: 5200,
    prompt_file: "use_cases.md",
    prompt_version: "1.3",
    input_summary: { signals: 12, rag_matches: 4 },
    output_summary: { use_cases_generated: 6, tiers: "2-LOW, 3-MEDIUM, 1-HIGH" },
    timestamp: "2026-03-16T12:00:11Z",
  },
  {
    agent_tag: "REPORT_WRITER",
    event: "agent_complete",
    latency_ms: 8700,
    prompt_file: "report_writer.md",
    prompt_version: "2.0",
    input_summary: { sections: 5, use_cases: 6 },
    output_summary: { total_chars: 3200, sections_complete: 5 },
    timestamp: "2026-03-16T12:00:16Z",
  },
];

// Collapsed by default — no runId needed to show the toggle
export const CollapsedDefault: Story = {
  args: {
    runId: "demo-run-123",
  },
};

// Pass mock data via a decorator that intercepts fetch
export const ExpandedWithMockData: Story = {
  args: {
    runId: "demo-run-123",
  },
  decorators: [
    (StoryFn) => {
      // Override fetch to return mock trace data immediately
      const originalFetch = global.fetch;
      global.fetch = async (input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/v1/trace/")) {
          return new Response(
            JSON.stringify({ run_id: "demo-run-123", stages: MOCK_STAGES }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          );
        }
        return originalFetch(input);
      };
      return <StoryFn />;
    },
  ],
};

export const NoRunId: Story = {
  args: {
    runId: null,
  },
};

export const ErrorState: Story = {
  args: {
    runId: "bad-run-404",
  },
  decorators: [
    (StoryFn) => {
      global.fetch = async () =>
        new Response(JSON.stringify({ detail: "not found" }), { status: 404 });
      return <StoryFn />;
    },
  ],
};
