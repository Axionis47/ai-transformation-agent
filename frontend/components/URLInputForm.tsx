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

  return (
    <form onSubmit={handleSubmit} className="neo-raised p-6 space-y-4">
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
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
          className="neo-inset w-full px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border focus:border-[#4f6df5] rounded-xl border border-transparent transition-colors disabled:opacity-50"
        />
      </div>
      <button
        type="submit"
        disabled={isLoading || !url.trim()}
        className="w-full rounded-xl py-3 text-sm font-semibold text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed neo-btn active:shadow-neo-btn-pressed"
        style={{ background: "#4f6df5" }}
        onMouseEnter={(e) => { if (!isLoading && url.trim()) (e.currentTarget as HTMLButtonElement).style.background = "#3b5de7"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "#4f6df5"; }}
      >
        {isLoading ? "Analyzing\u2026" : "Analyze"}
      </button>
      <div className="flex items-center gap-2">
        <input
          id="dry-run"
          type="checkbox"
          checked={dryRun}
          onChange={(e) => setDryRun(e.target.checked)}
          disabled={isLoading}
          className="h-3.5 w-3.5 accent-[#4f6df5]"
        />
        <label htmlFor="dry-run" className="text-xs text-gray-500">
          Dry run (fixture data — no API cost)
        </label>
      </div>
    </form>
  );
}
