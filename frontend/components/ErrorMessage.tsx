"use client";

interface ErrorMessageProps {
  message: string;
  onReset: () => void;
}

export default function ErrorMessage({ message, onReset }: ErrorMessageProps) {
  return (
    <div style={{ borderLeft: "2px solid var(--red)", paddingLeft: "1.25rem" }}>
      <p className="font-headline font-black text-ink mb-2" style={{ fontSize: "1.15rem" }}>
        Analysis failed
      </p>
      <p className="font-body text-ink-medium text-sm leading-relaxed mb-4">
        {message}
      </p>
      <div className="flex items-center gap-6">
        <button
          onClick={onReset}
          className="font-label uppercase text-xs bg-ink text-cream px-5 py-2 rounded-none transition-colors hover:bg-red"
        >
          Try Again
        </button>
        <button
          onClick={onReset}
          className="font-body text-ink-light text-sm underline hover:text-ink transition-colors"
        >
          New URL
        </button>
      </div>
    </div>
  );
}
