"use client";

import EvidencePanel from "@/components/EvidencePanel";
import type { VictoryMatch } from "@/lib/types";

interface ReportCardProps {
  title: string;
  content: string;
  wins?: VictoryMatch[];
  id?: string;
}

export default function ReportCard({ title, content, wins, id }: ReportCardProps) {
  return (
    <div id={id} className="py-8">
      {/* 1px rule above section title */}
      <div className="rule-ink mb-4" />

      {/* Section title */}
      <h2 className="font-label uppercase tracking-[0.12em] text-sm text-ink-light mt-6 mb-4">
        {title}
      </h2>

      {/* Body content */}
      <div
        className="font-body text-ink leading-[1.75] space-y-4"
        dangerouslySetInnerHTML={{ __html: formatContent(content) }}
      />

      {/* Evidence */}
      <EvidencePanel wins={wins ?? []} />
    </div>
  );
}

function formatContent(text: string): string {
  const blocks = text.split(/\n\n+/).filter(Boolean);

  return blocks
    .map((block) => {
      const trimmed = block.trim();

      if (/^\d+\.\s/.test(trimmed)) {
        const items = trimmed
          .split(/\n/)
          .filter(Boolean)
          .map((line) => {
            const content = line.replace(/^\d+\.\s*/, "");
            return `<li class="ml-1 text-ink">${formatInline(content)}</li>`;
          })
          .join("");
        return `<ol class="list-decimal list-inside space-y-1.5 pl-1 font-body text-ink">${items}</ol>`;
      }

      if (/^[-*]\s/.test(trimmed)) {
        const items = trimmed
          .split(/\n/)
          .filter(Boolean)
          .map((line) => {
            const content = line.replace(/^[-*]\s*/, "");
            return `<li class="ml-1 text-ink">${formatInline(content)}</li>`;
          })
          .join("");
        return `<ul class="list-disc list-inside space-y-1.5 pl-1 font-body text-ink">${items}</ul>`;
      }

      if (/^#{2,3}\s/.test(trimmed)) {
        const content = trimmed.replace(/^#{2,3}\s*/, "");
        return `<p class="font-headline text-ink font-bold mt-2">${formatInline(content)}</p>`;
      }

      const withBreaks = trimmed.replace(/\n/g, "<br/>");
      return `<p class="font-body text-ink">${formatInline(withBreaks)}</p>`;
    })
    .join("");
}

function formatInline(text: string): string {
  return text
    .replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="font-bold text-ink">$1</strong>'
    )
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(
      /`(.+?)`/g,
      '<code class="font-mono text-xs px-1.5 py-0.5" style="background:rgba(193,39,45,0.08)">$1</code>'
    );
}
