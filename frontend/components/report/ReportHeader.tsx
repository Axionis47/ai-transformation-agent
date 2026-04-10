import Link from "next/link";
import Badge from "@/components/ui/Badge";

export default function ReportHeader({
  runId,
  feedbackCount,
  opportunityCount,
  evidenceCount,
  onApprove,
  reviewAction,
  approved,
}: {
  runId: string;
  feedbackCount: number;
  opportunityCount: number;
  evidenceCount: number;
  onApprove: () => void;
  reviewAction: string | null;
  approved: boolean;
}) {
  return (
    <header className="h-12 bg-canvas-raised border-b border-edge-subtle flex items-center px-6 sticky top-0 z-20 print:hidden">
      <Link
        href={`/run/${runId}`}
        className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono"
      >
        &larr; Back to Run
      </Link>
      <div className="w-px h-4 bg-edge mx-4" />
      <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">
        Analysis Report
      </span>
      {feedbackCount > 0 && (
        <span className="ml-2">
          <Badge variant="indigo">Refined {feedbackCount}x</Badge>
        </span>
      )}
      <div className="flex-1" />
      <span className="text-2xs font-mono text-ink-tertiary mr-4">
        {opportunityCount} opportunities &middot; {evidenceCount} evidence
      </span>
      <button
        onClick={onApprove}
        disabled={!!reviewAction || approved}
        className="bg-mint text-ink-inverse px-4 py-1.5 text-2xs font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors"
      >
        {approved ? "Approved" : "Approve"}
      </button>
    </header>
  );
}
