import AnalyzeForm from "@/components/AnalyzeForm";

export default function HomePage() {
  return (
    <div className="space-y-7">
      {/* Hero section */}
      <div className="text-center space-y-4 pt-2">
        {/* Subtle badge */}
        <div className="inline-flex items-center gap-1.5 neo-flat px-3 py-1 rounded-full">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ background: "#4f6df5" }}
          />
          <span
            className="text-[10px] font-semibold tracking-widest uppercase"
            style={{ color: "#4f6df5" }}
          >
            AI-Powered Analysis
          </span>
        </div>

        {/* Primary headline */}
        <h1
          className="text-[2rem] leading-tight font-extrabold tracking-tight"
          style={{ color: "#1e2433" }}
        >
          AI Transformation Discovery
        </h1>

        {/* Supporting copy */}
        <p
          className="text-base leading-relaxed max-w-md mx-auto"
          style={{ color: "#4a5568" }}
        >
          Enterprise AI maturity assessment in 90 seconds — from URL to
          actionable roadmap.
        </p>
      </div>

      {/* Form */}
      <AnalyzeForm />
    </div>
  );
}
