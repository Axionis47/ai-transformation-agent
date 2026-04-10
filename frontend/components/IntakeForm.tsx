"use client";

import { useState } from "react";
import Spinner from "@/components/ui/Spinner";
import type { CompanyIntake, ReasoningConfig } from "@/lib/types";
import { SIZE_OPTIONS } from "@/config/constants";

interface IntakeFormProps {
  onSubmit: (data: CompanyIntake, config: ReasoningConfig) => void;
  loading: boolean;
  depth: number;
  threshold: number;
  onDepthChange: (v: number) => void;
  onThresholdChange: (v: number) => void;
}

const field =
  "w-full bg-canvas-inset border border-edge text-ink text-sm font-sans p-2.5 rounded focus:border-mint focus:outline-none transition-colors";
const sectionLabel = "text-xs text-ink-secondary uppercase tracking-wider font-medium";
const fieldLabel = "text-2xs text-ink-secondary uppercase tracking-wider mb-1.5 block font-medium";

export default function IntakeForm({
  onSubmit,
  loading,
  depth,
  threshold,
  onDepthChange,
  onThresholdChange,
}: IntakeFormProps) {
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [employeeBand, setEmployeeBand] = useState("");
  const [notes, setNotes] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(
      {
        company_name: companyName,
        industry,
        employee_count_band: employeeBand || undefined,
        notes: notes || undefined,
        constraints: [],
      },
      { reasoning_depth: depth, confidence_threshold: threshold },
    );
  }

  const ready = companyName.trim() && industry.trim();

  return (
    <form onSubmit={handleSubmit} className="space-y-0">
      {/* ── Section 1: Company Profile ── */}
      <div className="border border-edge-subtle rounded-md bg-canvas-raised">
        <div className="px-4 py-2.5 border-b border-edge-subtle flex items-center justify-between">
          <p className={sectionLabel}>Company Profile</p>
          <span className="text-2xs text-ink-secondary font-mono">01</span>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className={fieldLabel}>Company Name</label>
              <input
                type="text"
                className={field}
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                placeholder="Ramp"
              />
            </div>
            <div>
              <label className={fieldLabel}>Industry</label>
              <input
                type="text"
                className={field}
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                required
                placeholder="fintech"
              />
            </div>
            <div>
              <label className={fieldLabel}>Headcount Band</label>
              <select
                className={`${field} cursor-pointer`}
                value={employeeBand}
                onChange={(e) => setEmployeeBand(e.target.value)}
              >
                <option value="">—</option>
                {SIZE_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className={fieldLabel}>Analyst Notes</label>
            <textarea
              className={`${field} resize-none leading-relaxed`}
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Focus areas, constraints, known pain points, strategic context..."
            />
          </div>
        </div>
      </div>

      {/* ── Section 2: Analysis Parameters ── */}
      <div className="border border-edge-subtle rounded-md bg-canvas-raised mt-4">
        <div className="px-4 py-2.5 border-b border-edge-subtle flex items-center justify-between">
          <p className={sectionLabel}>Analysis Parameters</p>
          <span className="text-2xs text-ink-secondary font-mono">02</span>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 gap-6">
            {/* Depth control */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={fieldLabel}>Reasoning Depth</label>
                <span className="font-mono text-lg text-ink tabular">{depth}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                step={1}
                value={depth}
                onChange={(e) => onDepthChange(Number(e.target.value))}
                className="w-full h-1 bg-edge-subtle rounded-full appearance-none cursor-pointer accent-mint"
              />
              <div className="flex justify-between mt-1.5">
                <span className="text-2xs text-ink-secondary font-mono">1 QUICK</span>
                <span className="text-2xs text-ink-secondary font-mono">10 DEEP</span>
              </div>
              <p className="text-2xs text-ink-secondary/70 mt-2">
                Number of iterative reasoning loops. Higher values explore more evidence paths.
              </p>
            </div>

            {/* Confidence target */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={fieldLabel}>Confidence Target</label>
                <span className="font-mono text-lg text-ink tabular">
                  {(threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min={0.3}
                max={1.0}
                step={0.05}
                value={threshold}
                onChange={(e) => onThresholdChange(Number(e.target.value))}
                className="w-full h-1 bg-edge-subtle rounded-full appearance-none cursor-pointer accent-mint"
              />
              <div className="flex justify-between mt-1.5">
                <span className="text-2xs text-ink-secondary font-mono">30% EXPLORE</span>
                <span className="text-2xs text-ink-secondary font-mono">100% STRICT</span>
              </div>
              <p className="text-2xs text-ink-secondary/70 mt-2">
                Engine stops early when overall confidence exceeds this threshold.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 3: Execute ── */}
      <div className="border border-edge-subtle rounded-md bg-canvas-raised mt-4">
        <div className="px-4 py-2.5 border-b border-edge-subtle flex items-center justify-between">
          <p className={sectionLabel}>Execution</p>
          <span className="text-2xs text-ink-secondary font-mono">03</span>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-ink-secondary">
                {ready ? (
                  <>
                    <span className="text-ink font-medium">{companyName}</span> · {industry} ·{" "}
                    {depth} reasoning loops · target ≥{(threshold * 100).toFixed(0)}%
                  </>
                ) : (
                  "Enter company name and industry to begin analysis."
                )}
              </p>
            </div>
            <button
              type="submit"
              disabled={loading || !ready}
              className="bg-mint text-ink-inverse px-6 py-2 text-sm font-semibold rounded disabled:opacity-30 hover:bg-mint-bright transition-colors flex items-center gap-2 shrink-0"
            >
              {loading ? (
                <>
                  <Spinner size={14} />
                  Initializing...
                </>
              ) : (
                "Execute Analysis"
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
