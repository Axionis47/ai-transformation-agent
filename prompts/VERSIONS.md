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

## use_case_generator.md

| Version | Date | Description | ADR |
|---------|------|-------------|-----|
| 1.0 | 2026-03-16 | Initial prompt. Three-tier framework (LOW_HANGING_FRUIT/MEDIUM_SOLUTION/HARD_EXPERIMENT), data_flow required per use case, ROI calibration per tier, evidence tracing to signal_ids and win-NNN IDs. | — |
