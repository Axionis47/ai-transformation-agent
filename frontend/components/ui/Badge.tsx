interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "mint" | "amber" | "rose" | "indigo" | "muted";
}

const STYLES = {
  default: "bg-edge-subtle text-ink-secondary",
  mint: "bg-mint/15 text-mint",
  amber: "bg-amber/15 text-amber",
  rose: "bg-rose/15 text-rose",
  indigo: "bg-indigo/15 text-indigo",
  muted: "bg-canvas-overlay text-ink-tertiary",
};

export default function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-2xs font-mono font-medium ${STYLES[variant]}`}
    >
      {children}
    </span>
  );
}
