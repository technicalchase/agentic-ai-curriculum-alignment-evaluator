# Research Methodology

## Approach

Sprint One uses a **controlled benchmark design** grounded in the Technical Charter (Randall, 2026). Expected alignment classifications and diagnostic attribution labels are documented *before* the evaluator is run. This prevents post-hoc interpretation of results.

## Domain Anchor

All 10 synthetic scenarios are anchored to the COMPSCI 250 "even-even" (EE) regular expression problem (Randall, 2024, Appendix B). The problem asks students to:

1. Construct a regular expression for strings over {a, b} with an even number of a's **and** an even number of b's.
2. Justify that the construction is correct (completeness and soundness).

This is a well-defined problem with a known correct answer, making it suitable as a reproducible benchmark anchor.

## Revised Bloom's Taxonomy

Curriculum profiles use Revised Bloom's Taxonomy (Anderson & Krathwohl, 2001) to characterize the pedagogical target level:

- **UMass COMPSCI 250**: `Analyze` — students must decompose the structure of regular expressions and reason about formal language membership.
- **Japan Discrete Math**: `Understand` — students must correctly apply syntax and verify examples without formal proof.

The taxonomy provides a testable, shared framework for comparing expectations across profiles.

## Synthetic Profile Construction

Each institutional profile was constructed by:

1. Identifying Course Learning Outcomes (CLOs) relevant to the EE exercise.
2. Listing structural rules (prerequisites, proof requirements, formal standards) as `RuleItem` objects with unique `rule_id` values.
3. Listing socio-communicative norms (tone, guidance style) separately to prevent conflation with curriculum requirements.
4. Setting the Bloom baseline level.

## Benchmark Design

The 10 scenarios cover four categories:

| Category | Scenarios | Expected behaviour |
|---|---|---|
| Negative controls | EE_S01, EE_S02, EE_S06, EE_S08, EE_S09 | Both profiles agree on the same alignment status |
| Cross-profile differences | EE_S03, EE_S04, EE_S05, EE_S07, EE_S10 | Profiles disagree, triggering a contextual attribution |

**Negative controls** verify that the evaluator does not introduce spurious cross-profile differences when the feedback quality is profile-independent (either good for both or bad for both).

**Cross-profile scenarios** demonstrate that the same feedback can be appropriate in one curriculum context and inappropriate in another. These are the cases the evaluator is designed to identify.

## Evaluation Procedure

1. Expected labels are written into `scenarios.json` before any evaluation code runs.
2. The pipeline evaluates all 20 (scenario, profile) pairs and produces 10 paired comparisons.
3. Results are scored against the predefined labels.
4. All benchmark fixtures, expected labels, and results are retained in the repository.

## Accuracy Thresholds

| Measure | Threshold |
|---|---|
| Single-profile alignment accuracy (N=20) | ≥ 80% (16/20) |
| Paired attribution accuracy (N=10) | ≥ 80% (8/10) |

## Limitations

- The evaluation is deterministic pattern matching, not a trained model. The rules capture the design intent of each synthetic profile but may not generalise to new profiles without revision.
- The expected labels are themselves synthetic and represent the researcher's judgment. They are not empirically validated with educators.
- The Japan profile is fictional. No claims are made about actual Japanese educational institutions.
