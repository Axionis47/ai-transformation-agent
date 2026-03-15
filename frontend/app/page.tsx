import AnalyzeForm from "@/components/AnalyzeForm";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2 py-4">
        <p className="text-sm text-gray-500 max-w-xl mx-auto">
          Enter any company URL to generate an AI maturity assessment and
          transformation roadmap — powered by multi-agent analysis.
        </p>
      </div>
      <AnalyzeForm />
    </div>
  );
}
