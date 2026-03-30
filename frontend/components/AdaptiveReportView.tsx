"use client";
import { useState } from "react";
import type { AdaptiveReport, ReportOpportunity } from "@/lib/types";
import ConfidenceNarrative from "./ConfidenceNarrative";
import ReasoningChain from "./ReasoningChain";

const TIER: Record<string, string> = {
  easy: "bg-green-100 text-green-800 border-green-300",
  medium: "bg-amber-100 text-amber-800 border-amber-300",
  hard: "bg-red-100 text-red-800 border-red-300",
};
function OpportunitySection({ opp }: { opp: ReportOpportunity }) {
  const tier = opp.tier.toLowerCase();
  const style = TIER[tier] ?? "bg-gray-100 text-gray-800 border-gray-300";
  return (
    <div className="border border-gray-200 rounded-lg p-5 bg-white print:break-inside-avoid">
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{opp.title}</h3>
        <span className={`text-xs font-medium px-2 py-0.5 rounded border shrink-0 ${style}`}>
          {tier.charAt(0).toUpperCase() + tier.slice(1)}
        </span>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed mb-3">{opp.narrative}</p>
      <ConfidenceNarrative assessment="" confidence={opp.confidence} />
      <div className="mt-3 space-y-3">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
            Evidence Summary
          </p>
          <p className="text-sm text-gray-700">{opp.evidence_summary}</p>
        </div>
        {opp.risks.length > 0 && (
          <div className="bg-red-50 border-l-2 border-red-300 p-3 rounded-r">
            <p className="text-xs font-medium text-red-700 uppercase tracking-wider mb-1">Risks</p>
            <ul className="space-y-1">
              {opp.risks.map((r, i) => (
                <li key={i} className="text-sm text-red-800 flex items-start gap-1.5">
                  <span className="mt-1.5 w-1 h-1 bg-red-400 rounded-full shrink-0" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
            Recommended Approach
          </p>
          <p className="text-sm text-gray-700">{opp.recommended_approach}</p>
        </div>
      </div>
    </div>
  );
}

export default function AdaptiveReportView({ report }: { report: AdaptiveReport }) {
  const sorted = [...report.opportunities].sort((a, b) => b.confidence - a.confidence);
  const [chainOpen, setChainOpen] = useState(false);
  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6 bg-white text-gray-900 print:p-0">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
        <p className="text-xs font-medium text-indigo-600 uppercase tracking-wider mb-2">
          Key Insight
        </p>
        <p className="text-xl font-semibold text-indigo-900 leading-snug">{report.key_insight}</p>
      </div>
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">
          Executive Summary
        </h2>
        <p className="text-base text-gray-800 leading-relaxed">{report.executive_summary}</p>
      </div>
      <ConfidenceNarrative assessment={report.confidence_assessment} confidence={0} />
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
          Opportunities ({sorted.length})
        </h2>
        <div className="space-y-4">
          {sorted.map((opp, i) => (
            <OpportunitySection key={i} opp={opp} />
          ))}
        </div>
      </div>
      {report.what_we_dont_know.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
          <h2 className="text-sm font-medium text-amber-700 uppercase tracking-wider mb-2">
            What We Don&apos;t Know
          </h2>
          <ul className="space-y-1.5">
            {report.what_we_dont_know.map((item, i) => (
              <li key={i} className="text-sm text-amber-900 flex items-start gap-2">
                <span className="mt-1.5 w-1.5 h-1.5 bg-amber-400 rounded-full shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
      {report.recommended_next_steps.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">
            Recommended Next Steps
          </h2>
          <ol className="space-y-2">
            {report.recommended_next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-gray-800">
                <span className="bg-indigo-100 text-indigo-700 font-semibold text-xs w-6 h-6 flex items-center justify-center rounded-full shrink-0">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
      {report.reasoning_chain.length > 0 && (
        <div>
          <button
            onClick={() => setChainOpen(!chainOpen)}
            className="text-sm font-medium text-gray-500 uppercase tracking-wider flex items-center gap-2 hover:text-gray-700"
          >
            <span className={`transition-transform ${chainOpen ? "rotate-90" : ""}`}>&#9654;</span>
            Reasoning Chain
          </button>
          {chainOpen && (
            <div className="mt-3">
              <ReasoningChain steps={report.reasoning_chain} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
