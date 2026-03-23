interface DataRowProps {
  label: string
  value: string | number
}

export default function DataRow({ label, value }: DataRowProps) {
  return (
    <div className="flex justify-between items-baseline border-b border-border py-1.5">
      <span
        className="text-text-muted font-sans uppercase tracking-widest"
        style={{ fontSize: '12px', fontWeight: 500 }}
      >
        {label}
      </span>
      <span
        className="text-text-primary font-mono"
        style={{ fontSize: '14px', fontWeight: 500 }}
      >
        {typeof value === 'number' ? value.toFixed(2) : value}
      </span>
    </div>
  )
}
