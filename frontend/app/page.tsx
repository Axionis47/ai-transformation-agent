import AnalyzeForm from "@/components/AnalyzeForm";

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
    </>
  );
}
