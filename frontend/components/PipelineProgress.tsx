"use client";

const STEPS = ["Scraping", "Querying RAG", "Scoring maturity", "Writing report"];

export default function PipelineProgress() {
  return (
    <div className="neo-flat p-6 text-center">
      <p className="text-gray-500 text-sm animate-pulse">
        Running pipeline — this may take up to 90 seconds&hellip;
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {STEPS.map((step) => (
          <span key={step} className="neo-raised px-3 py-1 text-xs text-gray-400">
            {step}
          </span>
        ))}
      </div>
    </div>
  );
}
