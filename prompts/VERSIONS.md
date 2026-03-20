# Prompt Version Log

This file tracks all prompt versions across agents.
PM owns this file. Update at every prompt version bump.

## Format

| Version | Agent | Date | Description | ADR |
|---------|-------|------|-------------|-----|

---

## consultant.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-15 | Initial prompt. Dimension-based scoring, evidence-grounded use cases, RAG calibration, failure-mode guards, complete AnalysisResult schema. | ADR-006 |
| 2.0 | 2026-03-15 | Victory citation pattern. RAG Context Usage renamed to Tenex Delivery Win Citation. win-NNN IDs required (no fabrication). Wins are primary ROI evidence. Explicit alignment statements when industry/size/problem match. rag_matches schema: seed_id→win_id, solution_title→engagement_title. rag_benchmark now cites win-NNN. | — |

## report_writer.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-15 | Initial prompt. Audience-specific section rules (CEO/CTO/CFO/EM), structured use case format, ROI math requirements, 3-phase roadmap rules, failure-mode guards. | ADR-006 |

## signal_extractor.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-16 | Initial prompt. Extraction-only agent: seven signal types, confidence bands, verbatim raw_quote rule, no scoring or analysis, industry/scale always required. | -- |
| 1.1 | 2026-03-17 | Added process_signal, hiring_signal, pain_point extraction rules; clarified intent_signal triggers. | -- |

## maturity_scorer.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-16 | Initial prompt. Scores four dimensions from typed signals (not raw text), 0.5-increment composite, Developing ceiling guard, signals_used must reference real signal_ids. | — |
| 1.1 | 2026-03-17 | Added pain_point absence handling rule -- no penalty when pain points not publicly disclosed. | — |

## use_case_generator.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-16 | Initial prompt. Three-tier framework (LOW_HANGING_FRUIT/MEDIUM_SOLUTION/HARD_EXPERIMENT), data_flow required per use case, ROI calibration per tier, evidence tracing to signal_ids and win-NNN IDs. | — |

## tier1_delivered.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-19 | Initial prompt. Synthesizes use cases from DELIVERED MatchResult records (Library A direct matches). Requires exact win_id citation, proven metric verbatim, measurement_period, client_profile_summary match. Confidence always >= 0.80. Tier always LOW_HANGING_FRUIT. Includes failure guards against estimated language. | -- |

## tier2_adaptation.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-19 | Initial prompt. Synthesizes use cases from ADAPTATION MatchResult records (Library A adjacent matches). Requires base win_id citation, adaptation_notes explaining what changes, explicit discount factor on base ROI, gap_from_base in roi_basis. Confidence 0.55-0.79. Tier always MEDIUM_SOLUTION. | -- |

## tier3_ambitious.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-19 | Initial prompt. Synthesizes use cases from AMBITIOUS MatchResult records (Library B industry cases). Requires named external company or published source citation. Prohibits win-NNN citations. ROI always labeled as estimated with source. Confidence 0.40-0.65 hard cap. Tier always HARD_EXPERIMENT. | -- |

## pitch_brief.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-20 | Initial prompt. Five-section pre-meeting brief: opening_line, story, roi_conversation, questions, objection_prep. All numbers must trace to input data. Handles DELIVERED/ADAPTATION/AMBITIOUS match tiers with appropriate confidence labeling. Under-500-word output constraint. | -- |
