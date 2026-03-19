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
    <form onSubmit={handleSubmit} className="reveal-up delay-500">

      {/* Section label */}
      <span className="font-label uppercase tracking-[0.12em] text-xs text-ink-light font-semibold">
        Begin Assessment
      </span>

      {/* Input row: URL field + submit button */}
      <div className="mt-3 flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
        <input
          id="url"
          type="url"
          value={url}
          placeholder="https://stripe.com"
          onChange={(e) => setUrl(e.target.value)}
          disabled={isLoading}
          required
          className={[
            "font-mono text-sm flex-1",
            "border-0 border-b-[1.5px] border-ink bg-transparent",
            "focus:border-red outline-none py-2 px-0",
            "placeholder:text-ink-faint text-ink",
            "transition-colors",
            "disabled:opacity-40",
          ].join(" ")}
        />
        <button
          type="submit"
          disabled={!canSubmit}
          className={[
            "font-label uppercase tracking-[0.08em] text-sm font-bold",
            "bg-ink text-cream px-6 py-2.5",
            "hover:bg-red transition-colors",
            "rounded-none",
            !canSubmit ? "opacity-40 cursor-not-allowed" : "",
          ].join(" ")}
        >
          {isLoading ? "Analyzing..." : "Analyze \u2192"}
        </button>
      </div>

      {/* Meta row: dry-run checkbox + timing */}
      <div className="mt-3 flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            id="dry-run"
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
            disabled={isLoading}
            className="h-3.5 w-3.5 disabled:opacity-40"
            style={{ accentColor: "var(--red)" }}
          />
          <span className="font-mono text-xs text-ink-light select-none">
            Dry run — use fixture data
          </span>
        </label>
        <span className="font-mono text-xs text-red">avg. 87s</span>
      </div>

    </form>
  );
}
