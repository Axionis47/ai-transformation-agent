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
    <div id={id} className="neo-raised p-6">
      {/* Section header with accent underline */}
      <div className="mb-5 pb-4 border-b border-[#c4cad6]/50">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full" style={{ background: "#4f6df5" }} />
          <h2
            className="text-base font-bold tracking-tight"
            style={{ color: "#1e2433" }}
          >
            {title}
          </h2>
        </div>
      </div>

      {/* Content */}
      <div
        className="text-sm leading-7 space-y-4"
        style={{ color: "#4a5568" }}
        dangerouslySetInnerHTML={{ __html: formatContent(content) }}
      />

      {/* Evidence */}
      <EvidencePanel wins={wins ?? []} />
    </div>
  );
}

function formatContent(text: string): string {
  // Split into blocks on double newlines
  const blocks = text.split(/\n\n+/).filter(Boolean);

  return blocks
    .map((block) => {
      const trimmed = block.trim();

      // Numbered list block
      if (/^\d+\.\s/.test(trimmed)) {
        const items = trimmed
          .split(/\n/)
          .filter(Boolean)
          .map((line) => {
            const content = line.replace(/^\d+\.\s*/, "");
            return `<li class="ml-1">${formatInline(content)}</li>`;
          })
          .join("");
        return `<ol class="list-decimal list-inside space-y-1.5 pl-1">${items}</ol>`;
      }

      // Bullet list block
      if (/^[-*]\s/.test(trimmed)) {
        const items = trimmed
          .split(/\n/)
          .filter(Boolean)
          .map((line) => {
            const content = line.replace(/^[-*]\s*/, "");
            return `<li class="ml-1">${formatInline(content)}</li>`;
          })
          .join("");
        return `<ul class="list-disc list-inside space-y-1.5 pl-1">${items}</ul>`;
      }

      // Heading line (### or ## style)
      if (/^#{2,3}\s/.test(trimmed)) {
        const content = trimmed.replace(/^#{2,3}\s*/, "");
        return `<p class="font-semibold text-[#1e2433] mt-2">${formatInline(content)}</p>`;
      }

      // Regular paragraph — handle inline line breaks
      const withBreaks = trimmed.replace(/\n/g, "<br/>");
      return `<p>${formatInline(withBreaks)}</p>`;
    })
    .join("");
}

function formatInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-[#1e2433]">$1</strong>')
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>');
}
