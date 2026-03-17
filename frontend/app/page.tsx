import AnalyzeForm from "@/components/AnalyzeForm";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-3 pt-4">
        <div className="inline-block">
          <span className="neo-flat px-3 py-1 text-[10px] font-semibold tracking-widest uppercase text-[#4f6df5]">
            AI-Powered Analysis
          </span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
          AI Transformation Discovery
        </h1>
        <p className="text-base text-gray-500">
          Enterprise AI maturity assessment in 90 seconds
        </p>
      </div>
      <AnalyzeForm />
    </div>
  );
}
