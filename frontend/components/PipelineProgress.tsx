"use client";

import { useEffect, useState } from "react";

const STEPS = ["Scraping", "Querying RAG", "Scoring maturity", "Writing report"];

interface PipelineProgressProps {
  onCancel?: () => void;
}

export default function PipelineProgress({ onCancel }: PipelineProgressProps) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setActiveStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 18000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="neo-flat p-6 space-y-5">
      {/* Status line */}
      <div className="flex items-center gap-3">
        <span
          className="inline-block w-2 h-2 rounded-full animate-pulse flex-shrink-0"
          style={{ background: "#4f6df5" }}
        />
        <p className="text-sm font-semibold" style={{ color: "#1e2433" }}>
          Running pipeline&nbsp;&mdash; up to 90 seconds
        </p>
      </div>

      {/* Step indicators */}
      <div className="space-y-2">
        {STEPS.map((step, i) => {
          const done = i < activeStep;
          const active = i === activeStep;
          return (
            <div key={step} className="flex items-center gap-3">
              <span
                className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all"
                style={{
                  background: done
                    ? "#4f6df5"
                    : active
                    ? "rgba(79,109,245,0.15)"
                    : "rgba(0,0,0,0.06)",
                  color: done ? "#fff" : active ? "#4f6df5" : "#a0aec0",
                  boxShadow: active ? "0 0 0 2px rgba(79,109,245,0.3)" : "none",
                }}
              >
                {done ? "✓" : i + 1}
              </span>
              <span
                className="text-xs font-medium transition-colors"
                style={{
                  color: done ? "#4a5568" : active ? "#1e2433" : "#a0aec0",
                }}
              >
                {step}
              </span>
              {active && (
                <span
                  className="text-[10px] animate-pulse"
                  style={{ color: "#4f6df5" }}
                >
                  running&hellip;
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Cancel button */}
      {onCancel && (
        <div className="pt-1">
          <button
            onClick={onCancel}
            className="neo-flat px-4 py-2 text-xs font-medium rounded-neo-sm transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5] hover:shadow-neo-btn-pressed active:shadow-neo-btn-pressed"
            style={{ color: "#718096" }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
