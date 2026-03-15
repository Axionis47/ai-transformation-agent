"use client";

interface ReportCardProps {
  title: string;
  content: string;
}

export default function ReportCard({ title, content }: ReportCardProps) {
  // Split on double-newlines for paragraph breaks; treat **text** as bold
  const paragraphs = content.split(/\n\n+/).filter(Boolean);

  return (
    <div className="neo-raised p-6">
      <h2 className="text-base font-semibold text-gray-700 uppercase tracking-widest mb-4 pb-3 border-b border-neo-dark/20">
        {title}
      </h2>
      <div className="space-y-3 text-sm text-gray-600 leading-relaxed">
        {paragraphs.map((para, i) => (
          <p key={i} dangerouslySetInnerHTML={{ __html: formatParagraph(para) }} />
        ))}
      </div>
    </div>
  );
}

/** Bold **text** markers and preserve inline formatting */
function formatParagraph(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}
