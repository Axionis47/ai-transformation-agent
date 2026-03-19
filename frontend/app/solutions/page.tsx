import SolutionCard from "@/components/SolutionCard";
import { SOLUTIONS } from "@/lib/solutionsData";

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
            style={{ background: "#16a34a" }}
            aria-hidden="true"
          />
          <span
            className="text-[11px] font-semibold uppercase tracking-widest"
            style={{ color: "#16a34a" }}
          >
            Library A
          </span>
        </div>
        <h1
          className="text-2xl font-extrabold tracking-tight"
          style={{ color: "#1e2433" }}
        >
          Delivered Solutions
        </h1>
        <p className="text-sm" style={{ color: "#4a5568" }}>
          Tenex engagement history — proven AI deliveries
        </p>
      </div>

      {/* Stats bar */}
      <div className="neo-raised px-5 py-3 flex items-center gap-6">
        <div>
          <span
            className="text-xl font-bold"
            style={{ color: "#1e2433" }}
          >
            {SOLUTIONS.length}
          </span>
          <span
            className="text-xs ml-1.5"
            style={{ color: "#718096" }}
          >
            active engagements
          </span>
        </div>
        <div className="w-px h-5 bg-gray-200" />
        <div className="flex items-center gap-2">
          <span
            className="text-[11px] font-semibold px-2 py-0.5 rounded-full border"
            style={{
              background: "#f0fdf4",
              color: "#16a34a",
              borderColor: "#bbf7d0",
            }}
          >
            All Active
          </span>
          <span className="text-xs" style={{ color: "#718096" }}>
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
