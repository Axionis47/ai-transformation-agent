"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useReport, useApproveReport, useInvestigateDeeper, useRefineReport } from "@/lib/hooks";
import ReasoningChain from "@/components/ReasoningChain";
import ConfidenceNarrative from "@/components/ConfidenceNarrative";
import EvidenceAnnex from "@/components/EvidenceAnnex";
import FeedbackButton from "@/components/FeedbackButton";
import Spinner from "@/components/ui/Spinner";
import SectionHeader from "@/components/report/SectionHeader";
import OpportunityCard from "@/components/report/OpportunityCard";
import ReportHeader from "@/components/report/ReportHeader";
import ReportFooter from "@/components/report/ReportFooter";
import type { ReportFeedback } from "@/lib/types";
import { FEEDBACK_HIGHLIGHT_MS } from "@/config/constants";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;
  const [approved, setApproved] = useState(false);
  const [reviewAction, setReviewAction] = useState<string | null>(null);
  const [refining, setRefining] = useState(false);
  const [lastEdited, setLastEdited] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, error: loadError } = useReport(runId);
  const approveMutation = useApproveReport(runId);
  const investigateMutation = useInvestigateDeeper(runId);
  const refineMutation = useRefineReport(runId);

  const run = data?.run ?? null;
  const report = data?.report ?? null;
  const evidence = data?.evidence ?? [];

  const displayError = error || (loadError instanceof Error ? loadError.message : null);

  async function handleApprove() {
    setReviewAction("approving");
    setError(null);
    try {
      await approveMutation.mutateAsync();
      setApproved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setReviewAction(null);
    }
  }
  async function handleInvestigate() {
    setReviewAction("investigating");
    setError(null);
    try {
      await investigateMutation.mutateAsync();
      router.push(`/run/${runId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation request failed");
      setReviewAction(null);
    }
  }
  async function handleFeedback(feedback: ReportFeedback) {
    setRefining(true);
    setError(null);
    setLastEdited(null);
    try {
      await refineMutation.mutateAsync([feedback]);
      setLastEdited(feedback.target_section);
      setTimeout(() => setLastEdited(null), FEEDBACK_HIGHLIGHT_MS);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report refinement failed");
    } finally {
      setRefining(false);
    }
  }

  const feedbackCount = run?.feedback_history?.length ?? 0;
  const hl = (section: string) =>
    lastEdited === section
      ? "ring-1 ring-mint/40 bg-mint/5 transition-all duration-500"
      : "transition-all duration-500";

  // Loading / error / empty states
  const shell = (child: React.ReactNode) => (
    <div className="min-h-screen bg-canvas flex items-center justify-center">{child}</div>
  );
  if (!run && !displayError)
    return shell(
      <div className="flex flex-col items-center gap-3">
        <Spinner size={24} />
        <span className="text-2xs text-ink-tertiary font-mono">Loading report...</span>
      </div>,
    );
  if (displayError && !report) return shell(<p className="text-rose text-sm font-mono">{displayError}</p>);
  if (!report)
    return shell(
      <div className="text-center">
        <p className="text-ink-secondary text-sm">Report not yet generated.</p>
        <Link
          href={`/run/${runId}`}
          className="text-mint text-2xs font-mono mt-2 inline-block hover:text-mint-bright"
        >
          &larr; Back to run
        </Link>
      </div>,
    );

  const sorted = [...report.opportunities].sort((a, b) => b.confidence - a.confidence);
  const avgConfidence =
    sorted.length > 0 ? sorted.reduce((sum, o) => sum + o.confidence, 0) / sorted.length : 0;

  return (
    <div className="min-h-screen bg-canvas print:bg-white">
      <ReportHeader
        runId={runId}
        feedbackCount={feedbackCount}
        opportunityCount={sorted.length}
        evidenceCount={evidence.length}
        onApprove={handleApprove}
        reviewAction={reviewAction}
        approved={approved}
      />

      <main className="max-w-4xl mx-auto px-6 py-8 pb-16 print:p-0 print:max-w-none">
        {displayError && (
          <div className="bg-rose/10 border border-rose/20 rounded-md p-3 mb-6">
            <p className="text-sm text-rose font-mono">{displayError}</p>
          </div>
        )}
        {refining && (
          <div className="bg-mint/10 border border-mint/20 rounded-md p-3 mb-6 flex items-center gap-3">
            <Spinner size={14} />
            <p className="text-sm text-mint font-mono">Regenerating report...</p>
          </div>
        )}

        {/* 1. KEY INSIGHT */}
        <section className="mb-8">
          <p className="text-lg font-semibold text-ink leading-snug print:text-black">
            {report.key_insight}
          </p>
        </section>

        {/* 2. EXECUTIVE SUMMARY */}
        <section className={`mb-8 group rounded-md p-5 -mx-5 ${hl("executive_summary")}`}>
          <div className="flex items-center gap-3 mb-3">
            <SectionHeader
              action={
                <FeedbackButton targetSection="executive_summary" onSubmit={handleFeedback} />
              }
            >
              Executive Summary
            </SectionHeader>
          </div>
          <p className="text-sm text-ink leading-relaxed max-w-prose print:text-black">
            {report.executive_summary}
          </p>
        </section>

        {/* 3. OPPORTUNITIES */}
        <section className="mb-8">
          <SectionHeader>Opportunities ({sorted.length})</SectionHeader>
          <div className="space-y-3">
            {sorted.map((opp, i) => (
              <OpportunityCard
                key={opp.hypothesis_id || i}
                opp={opp}
                onFeedback={handleFeedback}
                highlighted={lastEdited === `opportunity:${opp.hypothesis_id}`}
                isStartingPoint={i === 0}
                defaultOpen={i === 0}
              />
            ))}
          </div>
        </section>

        {/* 4. IMPLEMENTATION ROADMAP */}
        {report.recommended_next_steps.length > 0 && (
          <section className={`mb-8 group rounded-md p-5 -mx-5 ${hl("next_steps")}`}>
            <SectionHeader
              action={<FeedbackButton targetSection="next_steps" onSubmit={handleFeedback} />}
            >
              Implementation Roadmap
            </SectionHeader>
            <ol className="space-y-3">
              {report.recommended_next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-ink print:text-black">
                  <span className="bg-indigo/15 text-indigo font-semibold text-xs w-6 h-6 flex items-center justify-center rounded-full shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* 5. REASONING CHAIN */}
        {report.reasoning_chain.length > 0 && (
          <section className="mb-8">
            <SectionHeader>How We Reached These Conclusions</SectionHeader>
            <ReasoningChain steps={report.reasoning_chain} />
          </section>
        )}

        {/* 6. CONFIDENCE ASSESSMENT */}
        <section className={`mb-8 group rounded-md p-5 -mx-5 ${hl("confidence")}`}>
          <SectionHeader
            action={<FeedbackButton targetSection="confidence" onSubmit={handleFeedback} />}
          >
            Confidence Assessment
          </SectionHeader>
          <ConfidenceNarrative
            assessment={report.confidence_assessment}
            confidence={avgConfidence}
          />
        </section>

        {/* 7. OPEN QUESTIONS */}
        {report.what_we_dont_know.length > 0 && (
          <section
            className={`mb-8 bg-amber/5 border border-amber/15 rounded-md p-5 group print:bg-white print:border-gray-300 ${hl("unknowns")}`}
          >
            <SectionHeader
              action={<FeedbackButton targetSection="unknowns" onSubmit={handleFeedback} />}
            >
              Open Questions &amp; Readiness Gaps
            </SectionHeader>
            <ul className="space-y-2">
              {report.what_we_dont_know.map((item, i) => (
                <li
                  key={i}
                  className="text-sm text-ink-secondary flex items-start gap-2 print:text-black leading-relaxed"
                >
                  <span className="mt-1.5 w-1.5 h-1.5 bg-amber rounded-full shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* 8. EVIDENCE ANNEX */}
        {evidence.length > 0 && <EvidenceAnnex evidence={evidence} />}
      </main>

      <ReportFooter
        runId={runId}
        approved={approved}
        reviewAction={reviewAction}
        onApprove={handleApprove}
        onInvestigate={handleInvestigate}
      />
    </div>
  );
}
