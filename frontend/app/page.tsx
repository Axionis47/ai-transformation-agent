import AnalyzeForm from "@/components/AnalyzeForm";

const PIPELINE_STAGES = [
  {
    num: "01",
    title: "SCRAPE",
    desc: "Fetches company pages, careers listings, and public data",
    time: "~12s",
  },
  {
    num: "02",
    title: "ANALYZE",
    desc: "Extracts AI readiness signals from scraped content",
    time: "~18s",
  },
  {
    num: "03",
    title: "SCORE",
    desc: "Scores maturity across four dimensions",
    time: "~15s",
  },
  {
    num: "04",
    title: "REPORT",
    desc: "Writes five-section transformation roadmap",
    time: "~25s",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Asymmetric two-column hero */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_0.72fr] gap-8 items-end">

        {/* Left column: kicker + headline */}
        <div className="reveal-up delay-150">
          <span className="font-label uppercase tracking-[0.15em] text-sm text-red">
            — AI-POWERED ANALYSIS
          </span>
          <h1
            className="font-headline font-black mt-3 text-ink"
            style={{ fontSize: "clamp(2.2rem, 4.5vw, 3.3rem)", lineHeight: 1.1 }}
          >
            Enterprise AI readiness,{" "}
            <em className="font-headline font-normal italic">diagnosed in seconds</em>
          </h1>
        </div>

        {/* Right column: two body paragraphs */}
        <div className="reveal-up delay-350 space-y-4">
          <p className="font-body text-ink-medium text-base leading-relaxed">
            Enter any company URL. Our four-agent pipeline scrapes public data,
            extracts signals, scores AI maturity, and writes a transformation
            roadmap in under 90 seconds.
          </p>
          <p className="font-body text-ink-medium text-base leading-relaxed">
            What used to cost $50K and take six weeks now runs for four cents.
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
          The Pipeline
        </h2>

        {/* 4-col on desktop, 2x2 on tablet, 1-col on mobile */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4">
          {PIPELINE_STAGES.map((stage, i) => (
            <div
              key={stage.title}
              className={[
                "py-6 pr-8",
                i < 3 ? "md:border-r border-rule" : "",
                i === 0 ? "sm:border-r border-rule" : "",
                i === 2 ? "sm:border-r border-rule" : "",
                i < 2 ? "border-b sm:border-b-0 md:border-b-0 border-rule" : "",
              ].join(" ")}
            >
              {/* Ghost number */}
              <span
                className="font-headline font-black block leading-none mb-3"
                style={{ fontSize: "3.5rem", color: "var(--ink-faint)" }}
              >
                {stage.num}
              </span>

              {/* Stage title */}
              <p className="font-label font-bold uppercase tracking-widest text-sm text-ink mb-2">
                {stage.title}
              </p>

              {/* Description */}
              <p className="font-body text-ink-medium text-sm leading-relaxed mb-4">
                {stage.desc}
              </p>

              {/* Timing tag */}
              <span className="font-mono text-xs text-red">
                {stage.time}
              </span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
