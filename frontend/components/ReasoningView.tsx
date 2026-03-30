"use client";

import { useState } from "react";
import type { ReasoningState } from "@/lib/types";
import DataRow from "./DataRow";

interface ReasoningViewProps {
  reasoningState: ReasoningState | null;
  onAnswer: (questionId: string, answer: string) => void;
  loading: boolean;
  depthBudget?: number;
}

export default function ReasoningView({
  reasoningState,
  onAnswer,
  loading,
  depthBudget = 3,
}: ReasoningViewProps) {
  const [answerText, setAnswerText] = useState("");

  if (!reasoningState) {
    return (
      <p className="text-text-muted font-mono" style={{ fontSize: "13px" }}>
        Waiting for reasoning state...
      </p>
    );
  }

  const {
    current_loop,
    field_coverage,
    overall_confidence,
    pending_question,
    completed,
    stop_reason,
    coverage_gaps,
  } = reasoningState;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pending_question || !answerText.trim()) return;
    onAnswer(pending_question.question_id, answerText);
    setAnswerText("");
  }

  return (
    <div className="space-y-2">
      {loading && (
        <p className="text-text-muted font-mono" style={{ fontSize: "12px" }}>
          Executing reasoning loop {current_loop}...
        </p>
      )}
      <DataRow label="Loop" value={`${current_loop} / ${depthBudget}`} />
      <DataRow label="Confidence" value={overall_confidence} />
      {Object.entries(field_coverage).map(([field, cov]) => (
        <DataRow key={field} label={field.replace(/_/g, " ")} value={cov} />
      ))}
      {pending_question && !completed && (
        <div className="pt-3 space-y-2">
          <p className="text-text-primary" style={{ fontSize: "14px" }}>
            {pending_question.question_text}
          </p>
          {pending_question.context && (
            <p className="text-text-muted font-mono" style={{ fontSize: "12px" }}>
              {pending_question.context}
            </p>
          )}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Your answer..."
              className="flex-1 bg-surface border border-border text-text-primary p-2 text-sm font-mono rounded-sm focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !answerText.trim()}
              className="bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50"
            >
              Submit
            </button>
          </form>
        </div>
      )}
      {completed && (
        <div className="pt-2 space-y-1">
          {stop_reason && <DataRow label="Stop Reason" value={stop_reason} />}
          {coverage_gaps.length > 0 && (
            <div>
              <p
                className="text-text-muted uppercase tracking-widest mb-1"
                style={{ fontSize: "12px" }}
              >
                Coverage Gaps
              </p>
              {coverage_gaps.map((g, i) => (
                <p key={i} className="text-text-muted font-mono" style={{ fontSize: "12px" }}>
                  {g}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
