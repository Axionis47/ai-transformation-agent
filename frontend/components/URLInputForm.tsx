"use client";

import { useState } from "react";

interface URLInputFormProps {
  onSubmit: (url: string, dryRun: boolean) => void;
  isLoading: boolean;
}

export default function URLInputForm({ onSubmit, isLoading }: URLInputFormProps) {
  const [url, setUrl] = useState("");
  const [dryRun, setDryRun] = useState(true);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit(url.trim(), dryRun);
  }

  const canSubmit = !isLoading && url.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="neo-raised p-6 space-y-4">
      {/* URL input */}
      <div>
        <label
          htmlFor="url"
          className="block text-sm font-semibold mb-2"
          style={{ color: "#1e2433" }}
        >
          Company URL
        </label>
        <input
          id="url"
          type="url"
          value={url}
          placeholder="https://stripe.com"
          onChange={(e) => setUrl(e.target.value)}
          disabled={isLoading}
          required
          className="neo-inset focus-accent w-full px-4 py-3 text-sm transition-all disabled:opacity-50"
          style={{ color: "#1e2433" }}
        />
      </div>

      {/* CTA button */}
      <button
        type="submit"
        disabled={!canSubmit}
        className="btn-accent w-full py-3 text-sm font-bold tracking-wide"
      >
        {isLoading ? "Analyzing\u2026" : "Analyze Company"}
      </button>

      {/* Dry-run toggle — quieter secondary element */}
      <div className="flex items-center gap-2 pt-0.5">
        <input
          id="dry-run"
          type="checkbox"
          checked={dryRun}
          onChange={(e) => setDryRun(e.target.checked)}
          disabled={isLoading}
          className="h-3.5 w-3.5 rounded accent-[#4f6df5] disabled:opacity-50"
        />
        <label
          htmlFor="dry-run"
          className="text-xs select-none"
          style={{ color: "#718096" }}
        >
          Dry run — use fixture data, no API cost
        </label>
      </div>
    </form>
  );
}
