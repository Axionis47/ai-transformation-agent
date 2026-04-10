export default function SectionHeader({
  children,
  action,
}: {
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">
        {children}
      </p>
      <div className="flex-1 border-t border-edge-subtle print:border-gray-300" />
      {action}
    </div>
  );
}
