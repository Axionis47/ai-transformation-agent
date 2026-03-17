"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getAnalysis } from "@/lib/history";
import type { AnalyzeSuccess } from "@/lib/types";
import ResultsView from "@/components/ResultsView";

export default function AnalysisResultPage() {
  const params = useParams();
  const runId = typeof params.runId === "string" ? params.runId : "";

  const [data, setData] = useState<AnalyzeSuccess | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const result = getAnalysis(runId);
    setData(result);
    setReady(true);
  }, [runId]);

  if (!ready) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="neo-flat px-8 py-6 text-center space-y-2">
          <p className="text-sm font-medium" style={{ color: "#4a5568" }}>
            Loading analysis...
          </p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="neo-flat px-8 py-8 text-center space-y-4 max-w-sm">
          <p
            className="text-base font-semibold"
            style={{ color: "#1e2433" }}
          >
            Analysis not found
          </p>
          <p className="text-sm" style={{ color: "#718096" }}>
            This run ID was not found in your local history. It may have
            been cleared or opened in a different browser.
          </p>
          <Link
            href="/"
            className="inline-block neo-btn px-6 py-2.5 text-sm font-semibold rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5]"
            style={{ color: "#4f6df5" }}
          >
            Run a new analysis
          </Link>
        </div>
      </div>
    );
  }

  return <ResultsView data={data} />;
}
