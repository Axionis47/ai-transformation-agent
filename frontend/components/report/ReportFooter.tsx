import Link from "next/link";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

export default function ReportFooter({
  runId,
  approved,
  reviewAction,
  onApprove,
  onInvestigate,
}: {
  runId: string;
  approved: boolean;
  reviewAction: string | null;
  onApprove: () => void;
  onInvestigate: () => void;
}) {
  return (
    <footer className="fixed bottom-0 left-0 right-0 bg-canvas-raised border-t border-edge-subtle px-6 py-3 flex items-center justify-end gap-3 z-20 print:hidden">
      {approved ? (
        <div className="flex items-center gap-3">
          <Badge variant="mint">Report Approved</Badge>
          <Link
            href={`/run/${runId}`}
            className="text-sm text-mint font-mono hover:text-mint-bright transition-colors"
          >
            Back to Run
          </Link>
        </div>
      ) : (
        <>
          <Link
            href={`/run/${runId}/enrich`}
            className="text-indigo text-2xs font-mono hover:text-indigo/80 transition-colors inline-flex items-center gap-1.5"
          >
            Enrich Analysis
          </Link>
          <button
            onClick={onInvestigate}
            disabled={!!reviewAction}
            className="bg-transparent border border-edge text-ink-secondary px-4 py-2 text-sm rounded-md disabled:opacity-40 hover:border-amber hover:text-amber transition-colors flex items-center gap-2"
          >
            {reviewAction === "investigating" ? (
              <>
                <Spinner size={14} />
                Requesting...
              </>
            ) : (
              "Investigate Deeper"
            )}
          </button>
          <button
            onClick={onApprove}
            disabled={!!reviewAction}
            className="bg-mint text-ink-inverse px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2"
          >
            {reviewAction === "approving" ? (
              <>
                <Spinner size={14} />
                Approving...
              </>
            ) : (
              "Approve Report"
            )}
          </button>
        </>
      )}
    </footer>
  );
}
