# Data Dictionary

Agentic AI Curriculum Alignment Evaluator

## Overview

This data dictionary documents every field used in the POC pipeline. It maps directly to the Pydantic models in `src/schemas.py` and to the JSON files in `data/`.

---

## Model: `InstitutionalProfile`

Stored in: `data/umass_cs250.json`, `data/japan_discrete_math.json`

| Field | Type / Allowed Values | Purpose & Guardrail Role |
|---|---|---|
| `profile_id` | `string` | Unique fixture identifier (`umass_cs250` or `japan_discrete_math`) |
| `institution_name` | `string` | Human-readable institution name |
| `structural_rules` | `list of RuleItem (rule_id, text)` | Verifiable curricular rules, prerequisites, and formal proof standards |
| `socio_communicative_norms` | `list of RuleItem (rule_id, text)` | Hypothetical cultural/communicative expectations (strictly isolated from structural rules) |
| `bloom_baseline_level` | `enum` (Anderson & Krathwohl, 2001): `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`, `Create` | Testable pedagogical target |

---

## Model: `RuleItem`

Sub-model used in `InstitutionalProfile`.

| Field | Type | Purpose |
|---|---|---|
| `rule_id` | `string` | Unique identifier used for citation verification. Naming convention: `<profile>_SR<n>` for structural rules, `<profile>_SCN<n>` for norms, `<profile>_CLO<n>` for CLOs. |
| `text` | `string` | Human-readable rule text |

---

## Model: `FeedbackScenario`

Stored in: `data/scenarios.json`

| Field | Type / Allowed Values | Purpose & Guardrail Role |
|---|---|---|
| `scenario_id` | `string` | Unique test case ID anchored to the COMPSCI 250 EE regular expression problem (e.g. `EE_S01`) |
| `student_attempt` | `string` | Synthetic student regular expression or proof snippet |
| `ai_feedback_text` | `string` | Synthetic AI feedback snippet held constant across both institutional profiles |
| `expected_umass_alignment` | `enum` (`Aligned`, `Misaligned`, `Insufficient_Information`) | Pre-defined expected alignment label for Profile A |
| `expected_japan_alignment` | `enum` (`Aligned`, `Misaligned`, `Insufficient_Information`) | Pre-defined expected alignment label for Profile B |
| `expected_attribution` | `enum` (`Consistent_With_Design_Limitation`, `Consistent_With_Contextual_Assumption`, `Insufficient_Information`) | Pre-defined expected paired attribution label |
| `is_negative_control` | `boolean` | `true` when profiles are not expected to differ in alignment outcome |

---

## Model: `DiagnosticClaim`

Sub-model used in `EvaluationResult`.

| Field | Type / Allowed Values | Purpose & Guardrail Role |
|---|---|---|
| `claim_text` | `string` | Specific observation about alignment or mismatch |
| `cited_ids` | `list of string (min 1)` | Exact `rule_id` or `scenario_id` verified by the deterministic citation critic |

---

## Model: `EvaluationResult`

Produced by: `AlignmentEngine.evaluate()`

| Field | Type / Allowed Values | Purpose & Guardrail Role |
|---|---|---|
| `scenario_id` | `string` | Paired feedback scenario identifier |
| `profile_id` | `string` | Institutional profile evaluated in this individual run |
| `alignment_status` | `enum` (`Aligned`, `Misaligned`, `Insufficient_Information`) | Single-profile alignment assessment prior to cross-profile comparison |
| `claims` | `list of DiagnosticClaim` | Grounded claims supporting the single-profile alignment assessment |
| `retry_count` | `int` (0–2) | Number of citation verification retries performed |

---

## Model: `PairedAttributionResult`

Produced by: `PairedComparisonEngine.compare()`

| Field | Type / Allowed Values | Purpose & Guardrail Role |
|---|---|---|
| `scenario_id` | `string` | Paired feedback scenario identifier (N=10) |
| `umass_result` | `EvaluationResult` | Institutional evaluation under Profile A (`umass_cs250`) |
| `japan_result` | `EvaluationResult` | Institutional evaluation under Profile B (`japan_discrete_math`) |
| `paired_attribution_label` | `enum` (3 non-causal labels) | `Consistent_With_Design_Limitation`, `Consistent_With_Contextual_Assumption`, or `Insufficient_Information` |
| `paired_rationale` | `string` | Cross-profile synthesis explaining why the paired outcomes support the attribution hypothesis |

---

## Rule ID Naming Conventions

| Prefix | Meaning |
|---|---|
| `umass_SR<n>` | UMass structural rule |
| `umass_SCN<n>` | UMass socio-communicative norm |
| `umass_CLO<n>` | UMass Course Learning Outcome |
| `japan_SR<n>` | Japan structural rule |
| `japan_SCN<n>` | Japan socio-communicative norm |
| `japan_CLO<n>` | Japan Course Learning Outcome |
| `EE_S<n>` | Scenario identifier (also a valid citation target) |
