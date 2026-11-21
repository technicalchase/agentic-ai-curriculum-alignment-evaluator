# Demo Walkthrough — Sprint One POC

**Agentic AI Curriculum Alignment Evaluator**

This walkthrough shows you how to run the POC end-to-end, understand what the
two curriculum profiles represent, and interpret the benchmark results.

---

## Prerequisites

- Python 3.10 or later
- Dependencies from `requirements.txt` in the repository root

```bash
pip install -r requirements.txt
```

The only external packages needed are `pydantic` (≥ 2.14) and `pytest` (≥ 9.2).
No API keys or internet access are required — the pipeline is fully deterministic.

---

## Running the pipeline

From the **repository root**, run:

```bash
python src/main.py
```

The script resolves all paths relative to the repository root, so it works
from any working directory as long as `src/main.py` is passed correctly.

What happens during the run:

1. **Input validation** — both curriculum profiles and all 10 scenarios are
   loaded from `data/` and validated by Pydantic. Invalid JSON or missing
   required fields will raise a `ValidationError` immediately.

2. **Alignment review** (Steps 2–3) — each of the 10 scenarios is evaluated
   against both profiles independently. The `AlignmentEngine` in `src/evaluator.py`
   applies deterministic rule-based checks against the feedback text and builds
   grounded `DiagnosticClaim` objects with explicit `cited_ids`.

3. **Citation verification** — the `CitationCritic` in `src/critic.py` checks
   that every `cited_id` in every claim resolves to a known `rule_id` in the
   relevant profile or the scenario's own `scenario_id`. Up to two retries are
   attempted; if unresolvable identifiers remain the result is downgraded to
   `Insufficient_Information`.

4. **Paired comparison** (Step 4) — the two single-profile results for each
   scenario are compared by the `PairedComparisonEngine` and assigned one of
   three attribution labels.

5. **Output** — results are written to:
   - `results/benchmark_report.json` — full structured output (Pydantic JSON)
   - `results/summary.txt` — human-readable evaluation report

Expected console output (abbreviated):

```
Loading curriculum profiles …
  ✓ umass_cs250
  ✓ japan_discrete_math
Loading feedback scenarios …
  ✓ 10 scenarios loaded

Running evaluations …
  EE_S01: UMass=Misaligned              Japan=Misaligned              → Consistent_With_Design_Limitation
  EE_S02: UMass=Aligned                 Japan=Aligned                 → Consistent_With_Design_Limitation
  EE_S03: UMass=Aligned                 Japan=Misaligned              → Consistent_With_Contextual_Assumption
  ...
```

---

## Running the automated tests

```bash
python -m pytest tests/ -v
```

The test suite has 38 tests across three files:

| File | What it covers |
|---|---|
| `tests/test_schemas.py` | Pydantic model validation — valid inputs, rejected invalid inputs, cross-field validators |
| `tests/test_critic.py` | `CitationCritic` — valid and invalid `cited_id` resolution |
| `tests/test_evaluator.py` | `AlignmentEngine`, `PairedComparisonEngine`, and end-to-end benchmark accuracy |

All 38 tests pass. No test modifies any source file or data fixture.

---

## The two curriculum profiles

Both profiles represent the **same problem** — constructing a regular expression
for the "even-even" (EE) language over `{a, b}`: strings containing an even number
of `a`'s **and** an even number of `b`'s.

### Profile A — `umass_cs250`

> *University of Massachusetts Amherst — COMPSCI 250: Introduction to Computation
> (Synthetic Profile)*

**Bloom's target level:** Analyze

**What this profile requires from AI feedback:**

- A correct answer must be accompanied by a **formal proof of correctness** —
  either a structural/inductive argument or a DFA-based derivation (SR02, SR04).
- Feedback on a wrong answer must **pinpoint the precise structural flaw** —
  not just mark it wrong or offer vague hints (SR07).
- **Finite automata** are assumed prerequisite knowledge; DFA-state explanations
  and state-elimination references are in scope (SR05, CLO01).
- Feedback may use technically precise language and counter-examples without
  extensive scaffolding (SCN01, SCN02).

### Profile B — `japan_discrete_math`

> *Hypothetical Japanese University — Discrete Mathematics for Computer Science
> (Synthetic Profile, Fictional)*

**Bloom's target level:** Understand

**What this profile requires from AI feedback:**

- Correctness is demonstrated through **example-based verification** against an
  acceptance table; a full formal proof is **not required** at this stage (SR02).
- **DFA concepts are out of scope** for this exercise — finite automata are
  introduced later in the course sequence (SR03, SR04).
- Demanding a formal inductive proof therefore **exceeds course expectations**
  and is considered misaligned (SR02, SR03).
- Feedback should use accessible language with plain-language paraphrases and
  positive framing (SCN02, SCN03).

### Why the two profiles diverge

The key difference is **prerequisite depth and proof expectations**:

| Dimension | UMass CS250 | Japan Discrete Math |
|---|---|---|
| Bloom level | Analyze | Understand |
| Formal proofs required | Yes (SR02, SR04) | No (SR02) |
| DFA knowledge assumed | Yes (SR05) | No (SR03, SR04) |
| Brief confirmation of correct answer | Misaligned — proof required | Aligned — verification sufficient |
| DFA-based explanation | Aligned | Misaligned — out of scope |

---

## Interpreting the benchmark results

### Attribution labels

Each of the 10 scenarios receives one of three **paired attribution labels**:

| Label | Decision rule | Meaning |
|---|---|---|
| `Consistent_With_Design_Limitation` | Both profiles agree (both Aligned or both Misaligned) | The feedback quality is curriculum-independent — either a system-level problem or universally good feedback |
| `Consistent_With_Contextual_Assumption` | Profiles disagree (one Aligned, one Misaligned) | The feedback embeds an assumption that holds in one curriculum context but not the other |
| `Insufficient_Information` | Either result is `Insufficient_Information` | Evidence is insufficient; flagged for human review |

> **Important**: These labels describe possible explanations, not confirmed
> causes. The system cannot determine *why* feedback was designed a certain way —
> it can only observe whether the feedback aligns with each profile's rules.

### Verified results (from `results/summary.txt`)

```
Single-profile alignment accuracy  (N=20): 20/20 = 100.0%  [target ≥80%]  ✓ PASS
Paired attribution accuracy        (N=10): 10/10 = 100.0%  [target ≥80%]  ✓ PASS
Cross-profile difference found            :                              ✓ PASS
All citations valid                        :                              ✓ PASS
```

### Per-scenario breakdown

| Scenario | UMass result | Japan result | Attribution | Note |
|---|---|---|---|---|
| EE_S01 | Misaligned | Misaligned | Design Limitation | Negative control — AI feedback contains a factually wrong "correct answer" |
| EE_S02 | Aligned | Aligned | Design Limitation | Negative control — correct answer confirmed accurately with explanation |
| EE_S03 | Aligned | Misaligned | Contextual Assumption | Feedback uses DFA + state-elimination (in-scope at UMass, out-of-scope at Japan) |
| EE_S04 | Misaligned | Aligned | Contextual Assumption | Plain-language hint without formal proof (misses UMass SR02; meets Japan SR02) |
| EE_S05 | Aligned | Misaligned | Contextual Assumption | Demands formal inductive proof (required at UMass; exceeds Japan SR02/SR03) |
| EE_S06 | Misaligned | Misaligned | Design Limitation | Negative control — feedback is self-contradictory |
| EE_S07 | Aligned | Misaligned | Contextual Assumption | Correct answer with DFA-state explanation (enriching at UMass; out-of-scope at Japan) |
| EE_S08 | Aligned | Aligned | Design Limitation | Negative control — structural diagnosis meets both curricula |
| EE_S09 | Aligned | Aligned | Design Limitation | Negative control — accurate structural diagnosis with test string |
| EE_S10 | Misaligned | Aligned | Contextual Assumption | Brief confirmation only — Japan accepts; UMass requires proof (SR02, SR04) |

### Negative controls

Five scenarios (EE_S01, EE_S02, EE_S06, EE_S08, EE_S09) are **negative controls**
that test whether the evaluator correctly handles cases where both profiles should
agree. All five returned the expected `Consistent_With_Design_Limitation` label,
confirming the evaluator does not manufacture spurious cross-profile differences.

### Cross-profile differences

Four scenarios (EE_S03, EE_S04, EE_S05, EE_S07, EE_S10) produced different
alignment outcomes across profiles — five total `Contextual_Assumption` cases.
These are the scenarios where the same feedback text aligns with one curriculum's
expectations but violates the other's.

---

## Project structure reference

```
├── data/
│   ├── umass_cs250.json          # Synthetic UMass COMPSCI 250 curriculum profile
│   ├── japan_discrete_math.json  # Synthetic Japanese university profile (fictional)
│   └── scenarios.json            # 10 synthetic feedback scenarios with ground-truth labels
├── src/
│   ├── schemas.py                # Pydantic data models
│   ├── critic.py                 # Deterministic citation verifier
│   ├── evaluator.py              # Alignment engine + paired comparison engine
│   └── main.py                   # Pipeline runner
├── tests/
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_schemas.py
│   ├── test_critic.py
│   └── test_evaluator.py
├── results/
│   ├── benchmark_report.json     # Full structured results
│   └── summary.txt               # Human-readable report
├── docs/                         # Architecture, methodology, and data dictionary
├── demo/
│   └── README.md                 # This walkthrough
└── requirements.txt
```

---

## Ethical boundaries

- No real student data is used. All scenarios, student responses, and AI feedback
  texts are synthetic.
- The Japan profile is fictional and does not represent any actual institution or
  national curriculum.
- The system does not grade students or send feedback to learners.
- Results are for researcher review only.
