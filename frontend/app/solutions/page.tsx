import SolutionCard from "@/components/SolutionCard";
import { SOLUTIONS } from "@/lib/solutionsData";
import { SOLUTIONS_ACCENT } from "@/lib/config";

export const metadata = {
  title: "Delivered Solutions | AI Transformation Discovery Agent",
  description:
    "Browse Tenex engagement history — proven AI deliveries from Library A.",
};

export default function SolutionsPage() {
  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ background: SOLUTIONS_ACCENT.green }}
            aria-hidden="true"
          />
          <span
            className="text-[11px] font-semibold uppercase tracking-widest"
            style={{ color: SOLUTIONS_ACCENT.green }}
          >
            Library A
          </span>
        </div>
        <h1
          className="text-2xl font-extrabold tracking-tight"
          style={{ color: SOLUTIONS_ACCENT.darkText }}
        >
          Delivered Solutions
        </h1>
        <p className="text-sm" style={{ color: SOLUTIONS_ACCENT.mutedText }}>
          Tenex engagement history — proven AI deliveries
        </p>
      </div>

      {/* Stats bar */}
      <div className="neo-raised px-5 py-3 flex items-center gap-6">
        <div>
          <span
            className="text-xl font-bold"
            style={{ color: SOLUTIONS_ACCENT.darkText }}
          >
            {SOLUTIONS.length}
          </span>
          <span
            className="text-xs ml-1.5"
            style={{ color: SOLUTIONS_ACCENT.grayText }}
          >
            active engagements
          </span>
        </div>
        <div className="w-px h-5 bg-gray-200" />
        <div className="flex items-center gap-2">
          <span
            className="text-[11px] font-semibold px-2 py-0.5 rounded-full border"
            style={{
              background: SOLUTIONS_ACCENT.metricBg,
              color: SOLUTIONS_ACCENT.green,
              borderColor: SOLUTIONS_ACCENT.metricBorder,
            }}
          >
            All Active
          </span>
          <span className="text-xs" style={{ color: SOLUTIONS_ACCENT.grayText }}>
            Tenex wins only
          </span>
        </div>
      </div>

      {/* Solution grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {SOLUTIONS.map((solution) => (
          <SolutionCard key={solution.id} solution={solution} />
        ))}
      </div>
    </div>
  );
}
