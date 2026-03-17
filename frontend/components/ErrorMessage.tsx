"use client";

interface ErrorMessageProps {
  message: string;
  onReset: () => void;
}

export default function ErrorMessage({ message, onReset }: ErrorMessageProps) {
  return (
    <div
      className="neo-raised p-5 space-y-3"
      style={{ borderLeft: "3px solid #e53e3e" }}
    >
      <div className="flex items-start gap-3">
        <span
          className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5"
          style={{ background: "#e53e3e" }}
        >
          !
        </span>
        <div className="space-y-1">
          <p className="text-sm font-semibold" style={{ color: "#c53030" }}>
            Analysis failed
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#744210" }}>
            {message}
          </p>
        </div>
      </div>

      <button
        onClick={onReset}
        className="btn-accent px-5 py-2 text-xs font-semibold"
        style={{
          background: "linear-gradient(135deg, #fc8181, #e53e3e)",
          boxShadow: "3px 3px 10px rgba(229,62,62,0.35), -2px -2px 6px rgba(255,255,255,0.8)",
        }}
      >
        Try again
      </button>
    </div>
  );
}
