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
    <form onSubmit={handleSubmit} className="neo-raised p-8 space-y-5">
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-600 mb-2">
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
          className="neo-inset w-full px-4 py-3 text-sm text-gray-700 placeholder-gray-400 focus:outline-none disabled:opacity-50"
        />
      </div>
      <div className="flex items-center gap-3">
        <input
          id="dry-run"
          type="checkbox"
          checked={dryRun}
          onChange={(e) => setDryRun(e.target.checked)}
          disabled={isLoading}
          className="h-4 w-4 accent-gray-600"
        />
        <label htmlFor="dry-run" className="text-sm text-gray-500">
          Dry run (fixture data — no API cost)
        </label>
      </div>
      <button
        type="submit"
        disabled={isLoading || !url.trim()}
        className="neo-flat px-8 py-3 text-sm font-semibold text-gray-700 hover:shadow-neo-raised transition-shadow disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isLoading ? "Analyzing\u2026" : "Analyze"}
      </button>
    </form>
  );
}
