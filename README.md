# agentic-ai-curriculum-alignment-evaluator

Agentic AI proof of concept (POC) developed using IBM Bob to evaluate AI generated educational feedback against different curriculum expectations. Using 10 synthetic scenarios and two curriculum profiles, the POC examines whether feedback supports learning, identifies possible gaps in system design, and provides evidence for human review.

## Overview

The evaluator takes AI-generated feedback on the COMPSCI 250 "even-even" (EE) regular expression problem and checks whether that feedback aligns with the expectations of two synthetic institutional profiles:

- **Profile A** (`umass_cs250`): Loosely based on UMass Amherst COMPSCI 250, which requires formal proof justification and DFA-level reasoning.
- **Profile B** (`japan_discrete_math`): A fictional comparison profile with weaker prerequisites and different communication preferences.

Each feedback scenario is evaluated against both profiles, and the two results are compared to assign one of three diagnostic attribution labels:

| Label | Meaning |
|---|---|
| `Consistent_With_Design_Limitation` | Feedback fails (or succeeds) regardless of curriculum context |
| `Consistent_With_Contextual_Assumption` | Feedback works in one context but not the other |
| `Insufficient_Information` | Evidence is insufficient; flagged for human review |

> **Important**: These labels describe possible explanations, not confirmed causes.

## Quickstart

### Prerequisites

- Python 3.10+
- `pydantic` and `pytest`

```bash
pip install pydantic pytest
```

### Run the pipeline

```bash
python src/main.py
```

This will:
1. Load and validate the two curriculum profiles and 10 scenarios
2. Run 20 institutional evaluations (10 scenarios × 2 profiles)
3. Run 10 paired comparisons
4. Score results against predefined ground-truth labels
5. Save `results/benchmark_report.json` and `results/summary.txt`

### Run the tests

```bash
python -m pytest tests/ -v
```

## Demo

See [`demo/README.md`](demo/README.md) for a step-by-step walkthrough that covers:

- How to run the pipeline and the test suite
- What the two curriculum profiles represent and how they differ
- How to interpret the three attribution labels and the per-scenario results

## Project Structure

```
├── data/
│   ├── umass_cs250.json          # Synthetic UMass COMPSCI 250 curriculum profile
│   ├── japan_discrete_math.json  # Synthetic Japanese university profile (fictional)
│   └── scenarios.json            # 10 synthetic feedback scenarios with ground-truth labels
├── src/
│   ├── schemas.py                # Pydantic data models (InstitutionalProfile, FeedbackScenario, etc.)
│   ├── critic.py                 # Deterministic citation verifier (CitationCritic)
│   ├── evaluator.py              # Alignment engine + paired comparison engine
│   └── main.py                   # Pipeline runner (Steps 1–4)
├── tests/
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_schemas.py           # Schema validation tests
│   ├── test_critic.py            # Citation verification tests
│   └── test_evaluator.py         # Alignment and benchmark accuracy tests
├── results/
│   ├── benchmark_report.json     # Full structured results (Pydantic JSON)
│   └── summary.txt               # Human-readable evaluation report
├── demo/
│   └── README.md                 # Step-by-step demo walkthrough
└── docs/
    ├── architecture.md
    ├── data_dictionary.md
    ├── methodology.md
    ├── problem_solution.md
    ├── related_publications.md
    └── technology_statement.md
```

## Acceptance Criteria

| Criterion | Target | Result |
|---|---|---|
| Single-profile alignment accuracy (N=20) | ≥ 80% (16/20) | ✓ 20/20 = 100% |
| Paired attribution accuracy (N=10) | ≥ 80% (8/10) | ✓ 10/10 = 100% |
| Cross-profile difference found | At least 1 | ✓ Yes |
| All citations valid | 100% | ✓ Yes |

## Pipeline Architecture

The four-step pipeline (Technical Charter, Section 2):

```
1. Input validation (Pydantic)   → schemas.py
2. Alignment review              → evaluator.py AlignmentEngine
3. Citation check (up to 2 retries) → critic.py CitationCritic
4. Paired comparison + report    → evaluator.py PairedComparisonEngine
```

## Ethical Boundaries

- No real student data is used. All scenarios, student responses, and feedback are synthetic.
- The Japan profile is fictional and does not represent any actual institution.
- The system does not grade students or send feedback to learners.
- Results are for researcher review only.

## Citation

Randall, A. K. C. (2026). *Sprint One POC Technical Charter: Agentic AI Curriculum Alignment Evaluator*. IBM SkillsBuild AI Experiential Learning Lab.
