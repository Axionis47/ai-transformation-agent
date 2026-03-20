import AnalyzeForm from "@/components/AnalyzeForm";
import { PIPELINE_STAGES, STRINGS } from "@/lib/config";

export default function HomePage() {
  return (
    <>
      {/* Asymmetric two-column hero */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_0.72fr] gap-8 items-end">

        {/* Left column: kicker + headline */}
        <div className="reveal-up delay-150">
          <span className="font-label uppercase tracking-[0.15em] text-sm text-red">
            {STRINGS.kicker}
          </span>
          <h1
            className="font-headline font-black mt-3 text-ink"
            style={{ fontSize: "clamp(2.2rem, 4.5vw, 3.3rem)", lineHeight: 1.1 }}
          >
            {STRINGS.headline}{" "}
            <em className="font-headline font-normal italic">{STRINGS.headlineItalic}</em>
          </h1>
        </div>

        {/* Right column: two body paragraphs */}
        <div className="reveal-up delay-350 space-y-4">
          <p className="font-body text-ink-medium text-base leading-relaxed">
            {STRINGS.heroBody1}
          </p>
          <p className="font-body text-ink-medium text-base leading-relaxed">
            {STRINGS.heroBody2}
          </p>
        </div>

      </div>

      {/* Double rule separator */}
      <div className="rule-double my-10" />

      {/* Input section */}
      <AnalyzeForm />

      {/* Double rule before pipeline section */}
      <div className="rule-double my-10" />

      {/* The Pipeline section */}
      <section className="reveal-up delay-500">
        <h2 className="font-headline font-black text-ink mb-8" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)" }}>
          {STRINGS.pipelineTitle}
        </h2>

        {/* 3-col on desktop, 2-col on tablet, 1-col on mobile */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
          {PIPELINE_STAGES.map((stage, i) => (
            <div
              key={stage.title}
              className={[
                "py-6 pr-8",
                (i % 3 !== 2) ? "md:border-r border-rule" : "",
                (i % 2 === 0) ? "sm:border-r md:border-r-0 border-rule" : "",
                (i % 3 !== 2) ? "" : "",
                i < 3 ? "border-b border-rule md:border-b" : "",
              ].filter(Boolean).join(" ")}
            >
              <span
                className="font-headline font-black block leading-none mb-3"
                style={{ fontSize: "3.5rem", color: "var(--ink-faint)" }}
              >
                {stage.num}
              </span>
              <p className="font-label font-bold uppercase tracking-widest text-sm text-ink mb-2">
                {stage.title}
              </p>
              <p className="font-body text-ink-medium text-sm leading-relaxed">
                {stage.desc}
              </p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
