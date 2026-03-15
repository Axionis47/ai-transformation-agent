"use client";

interface ErrorMessageProps {
  message: string;
  onReset: () => void;
}

export default function ErrorMessage({ message, onReset }: ErrorMessageProps) {
  return (
    <div className="neo-raised p-6 border-l-4 border-red-400">
      <p className="text-sm font-semibold text-red-700">Analysis failed</p>
      <p className="text-sm text-red-600 mt-1">{message}</p>
      <button
        onClick={onReset}
        className="mt-3 text-xs text-gray-500 underline hover:text-gray-700"
      >
        Try again
      </button>
    </div>
  );
}
