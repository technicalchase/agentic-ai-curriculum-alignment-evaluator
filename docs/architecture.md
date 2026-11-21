# Code Architecture

## Overview

The POC is implemented as a pure Python package with no external API calls. All evaluation logic is deterministic and reproducible. The pipeline follows the four-step design in the Sprint One Technical Charter (Randall, 2026).

## Module Map

```
src/
├── schemas.py    — Pydantic data models (Step 1: validation)
├── critic.py     — CitationCritic (Step 3: citation verification)
├── evaluator.py  — AlignmentEngine + PairedComparisonEngine (Steps 2 & 4)
└── main.py       — Pipeline orchestrator and report writer
```

## Step 1 — Input Validation (`schemas.py`)

All data entering the pipeline is validated by Pydantic models on construction. Invalid inputs are rejected with a `ValidationError` rather than silently coerced.

| Model | Purpose |
|---|---|
| `RuleItem` | A single curriculum rule with a verifiable `rule_id` |
| `InstitutionalProfile` | Full curriculum profile (structural rules + communicative norms + Bloom level) |
| `FeedbackScenario` | One synthetic test case (student attempt + AI feedback + expected labels) |
| `DiagnosticClaim` | A grounded observation with cited identifiers |
| `EvaluationResult` | Single-profile alignment result for one (scenario, profile) pair |
| `PairedAttributionResult` | Cross-profile comparison for one scenario |
| `BenchmarkReport` | Top-level output saved to `results/` |

## Step 2 — Alignment Review (`evaluator.py` → `AlignmentEngine`)

For each (scenario, profile) pair the `AlignmentEngine` compares the `ai_feedback_text` against the profile's structural rules and communicative norms using lightweight deterministic pattern matching. The logic is fully auditable from the source code.

**UMass COMPSCI 250 rules:**
- `U-A`: Incorrect-answer feedback must identify the structural flaw (SR07).
- `U-B`: Correct-answer feedback must require or provide proof justification (SR02, SR04).
- `U-C`: Correct answer with explanation → Aligned (SR02, CLO01).
- `U-D`: Incorrect-answer feedback with structural diagnosis or proof → Aligned (SR07); hint-only → Misaligned (SR07, SR02).

**Japan Discrete Math rules:**
- `J-0`: Feedback that incorrectly rejects a correct answer → Misaligned (CLO01, SR01).
- `J-A`: DFA/automata references are out-of-scope → Misaligned (SR03, SR04).
- `J-B`: Formal proof demands exceed course level → Misaligned (SR02, SR03).
- `J-C`: Error feedback in accessible language → Aligned (SR05, CLO02).
- `J-D/E`: Correct-answer confirmation (with or without explanation) → Aligned (CLO01, CLO02).

**Universal rule (both profiles):**
- `U1`: Self-contradictory feedback → Misaligned regardless of curriculum.

## Step 3 — Citation Verification (`critic.py` → `CitationCritic`)

After claims are generated, every `cited_id` in every `DiagnosticClaim` is verified against the pool of valid identifiers for the current (profile, scenario) pair. Valid identifiers are:
- `rule_id` values from `structural_rules` and `socio_communicative_norms`
- The `scenario_id` of the current scenario

If any citation is invalid, the evaluator retries up to **2 times** (stripping claims with bad citations). If the result still contains invalid citations after retries, the `EvaluationResult` is downgraded to `Insufficient_Information`.

## Step 4 — Paired Comparison (`evaluator.py` → `PairedComparisonEngine`)

The two `EvaluationResult` objects for each scenario are compared:

| UMass status | Japan status | Label |
|---|---|---|
| Misaligned | Misaligned | `Consistent_With_Design_Limitation` |
| Aligned | Aligned | `Consistent_With_Design_Limitation` |
| Aligned | Misaligned | `Consistent_With_Contextual_Assumption` |
| Misaligned | Aligned | `Consistent_With_Contextual_Assumption` |
| Either `Insufficient_Information` | — | `Insufficient_Information` |

## Data Flow

```
data/umass_cs250.json ──────────────────────────┐
data/japan_discrete_math.json ──────────────────┤
                                                 ▼
data/scenarios.json ──────► main.py ──► AlignmentEngine × 2
                                              │
                                         CitationCritic
                                              │
                                    PairedComparisonEngine
                                              │
                                    BenchmarkReport
                                              │
                              results/benchmark_report.json
                              results/summary.txt
```
