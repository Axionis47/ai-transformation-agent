"use client";

import EvidencePanel from "@/components/EvidencePanel";
import type { VictoryMatch } from "@/lib/types";

interface ReportCardProps {
  title: string;
  content: string;
  wins?: VictoryMatch[];
}

export default function ReportCard({ title, content, wins }: ReportCardProps) {
  const paragraphs = content.split(/\n\n+/).filter(Boolean);

  return (
    <div className="neo-raised p-5">
      <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-widest mb-3 pb-3 border-b border-neo-dark/20">
        {title}
      </h2>
      <div className="space-y-3 text-sm text-gray-600 leading-relaxed">
        {paragraphs.map((para, i) => (
          <p key={i} dangerouslySetInnerHTML={{ __html: formatParagraph(para) }} />
        ))}
      </div>
      <EvidencePanel wins={wins ?? []} />
    </div>
  );
}

function formatParagraph(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}
