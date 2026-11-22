# PoC Design Rationale

## Overview

This document explains how the original research problem, proposed solution, and value proposition articulated in the [IBM AI Experiential Learning Lab Mid-Program Milestone Checkpoint](IBM_MidProgram_CheckPoint_Sumary.pdf) informed the design and implementation of the Sprint One proof of concept (POC).

The checkpoint was submitted before development began. It represents the researcher's formal statement of intent — the "why" behind the project. This document traces the path from that statement to the working system.

---

## 1. From Industry Challenge to Research Question

### Checkpoint Statement

The mid-program checkpoint identified the following industry challenge:

> *Developing an Agentic AI system that distinguishes between design limitations and assumptions that do not generalize across educational contexts.*

The challenge focused on AI-supported adaptive learning environments. When these systems fail to provide meaningful feedback or support, it is often unclear whether the problem originates from the system's design or from assumptions about learners, curricula, and educational settings.

### How This Shaped the PoC

This challenge became the POC's core research question:

> **When an AI learning system fails a learner, are we questioning the learner or questioning the system?**

The Sprint One evaluator operationalizes this question by taking AI-generated feedback on a well-defined discrete mathematics problem and checking whether that feedback aligns with two different institutional curriculum profiles. The evaluator surfaces two types of explanations for human review:

- **Design limitations** — feedback that fails (or succeeds) regardless of which curriculum is applied, suggesting a problem in the AI system itself.
- **Contextual assumptions** — feedback that works in one curriculum context but not another, suggesting the AI was implicitly designed for a specific educational setting.

These two labels map directly to the original challenge: distinguishing design limitations from non-generalizing assumptions.

---

## 2. From Preliminary Idea to Implementation

### Checkpoint Statement

The checkpoint described the preliminary idea as:

> *An Agentic AI system that examines cases where an AI-supported educational system produces feedback that may not be meaningful or appropriate for a particular learning environment. Rather than treating every failure as a technical problem, the agent considers whether the observed behavior reflects a limitation in the system's design or an assumption that does not hold across different educational settings.*

Development was planned to begin following the milestone submission, using **IBM Bob** to build a small proof of concept with structured scenarios that demonstrate how AI agents analyze system behavior, compare possible explanations, and produce reasoned assessments.

### How This Shaped the PoC

The Sprint One POC translates this preliminary idea into a concrete, fully reproducible implementation:

| Checkpoint Concept | Sprint One Implementation |
|---|---|
| Structured scenarios | 10 synthetic feedback scenarios anchored to the COMPSCI 250 "even-even" regular expression problem (`data/scenarios.json`) |
| Compare possible explanations | Deterministic `AlignmentEngine` evaluates each scenario against two curriculum profiles and returns a grounded `EvaluationResult` |
| Reasoned assessments of potential causes | `PairedComparisonEngine` compares results across profiles and assigns one of three diagnostic attribution labels |
| Produce evidence for human review | `BenchmarkReport` saved to `results/` with full citation grounding for every diagnostic claim |
| Use IBM Bob for development | IBM Bob served as the primary development environment throughout Sprint One (see [`technology_statement.md`](technology_statement.md)) |

The choice to anchor all scenarios to a single, well-defined problem (the EE regular expression exercise) reflects the checkpoint's emphasis on "structured scenarios" — a controlled environment where the evaluator's behavior can be verified and reproduced without ambiguity.

---

## 3. From Value Proposition to Design Decisions

### Checkpoint Statement

The checkpoint articulated the value proposition as follows:

> *For researchers, educators, administrators, developers of adaptive learning systems, and other stakeholders invested in learner success who need to understand why AI-supported educational systems behave differently across contexts, our agent delivers an analysis that distinguishes between design limitations and assumptions that do not generalize across educational settings.*

The checkpoint also emphasized two modes of human involvement:

- **Human in the loop:** Humans actively participate in reviewing or making decisions.
- **Human on the loop:** Humans oversee the system and intervene when necessary.

### How This Shaped the PoC

Three design decisions in the Sprint One POC trace directly to this value proposition:

**Decision 1 — Deterministic rule-based evaluation (not a trained model)**

The `AlignmentEngine` uses explicit, auditable pattern matching rather than a live language model. This was a deliberate choice to ensure that every result can be fully traced to documented curriculum rules — a prerequisite for meaningful human review. A "black-box" evaluator would undermine the human-in-the-loop and human-on-the-loop commitments stated in the checkpoint.

**Decision 2 — Citation grounding for every diagnostic claim**

Every `DiagnosticClaim` produced by the evaluator must cite a verifiable `rule_id` or `scenario_id`. The `CitationCritic` enforces this by verifying citations after each evaluation. If valid citations cannot be provided, the result is downgraded to `Insufficient_Information` and flagged for human review. This design directly supports the checkpoint's goal of making "underlying assumptions more visible."

**Decision 3 — Three-label attribution taxonomy**

The checkpoint's core distinction — design limitation versus non-generalizing assumption — maps to two of the three diagnostic labels:

| Attribution Label | Checkpoint Concept |
|---|---|
| `Consistent_With_Design_Limitation` | Feedback behavior is profile-independent — a property of the AI system's design |
| `Consistent_With_Contextual_Assumption` | Feedback behavior differs across profiles — a contextual assumption that does not generalize |
| `Insufficient_Information` | Evidence is insufficient; flagged for human review — directly supports human-on-the-loop oversight |

---

## 4. From AI-Use Justification to Technical Scope

### Checkpoint Statement

The checkpoint justified the use of AI by noting that the challenge involves evidence that:

> *...differs in volume, structure, format, and meaning. Curriculum documents, expert interviews, learner feedback, and system performance data may reveal patterns difficult to see in isolation. Differences in terminology, cultural norms, and educational contexts complicate comparisons.*

It also acknowledged a key limitation:

> *Agentic AI does not automatically resolve data incompatibility or guarantee that identified patterns are meaningful. Its value lies in its ability to coordinate analysis across different sources, identify possible relationships, and present explanations for human evaluation.*

### How This Shaped the PoC

The Sprint One POC reflects the checkpoint's honest framing of AI's value and limits:

- The evaluation is deterministic pattern matching, not a trained model. The rules capture the design intent of each synthetic profile but may not generalize to new profiles without revision.
- The expected labels are themselves synthetic and represent the researcher's judgment. They are not empirically validated with educators.
- The Japan profile is fictional. No claims are made about actual Japanese educational institutions.
- Results are for researcher and educator review only. The system does not grade students or send feedback to learners.

The POC is intentionally scoped to demonstrate the feasibility of the approach, not to replace human judgment. This is consistent with the checkpoint's statement that "the goal becomes not to replace human evaluation but to check overreliance on AI."

---

## 5. Progression from Checkpoint to Working System

The following table summarizes the progression from the checkpoint's statements to the working Sprint One POC:

| Stage | Artifact | Description |
|---|---|---|
| Program entry | [`IBM_MidProgram_CheckPoint_Sumary.pdf`](IBM_MidProgram_CheckPoint_Sumary.pdf) | Original challenge, preliminary idea, value proposition, and AI-use justification submitted before development began |
| Problem formalization | [`problem_solution.md`](problem_solution.md) | Research question, solution framing, and scope boundaries derived from the checkpoint |
| Methodology design | [`methodology.md`](methodology.md) | Controlled benchmark design, synthetic profile construction, and accuracy thresholds |
| System architecture | [`architecture.md`](architecture.md) | Four-step pipeline design and module map |
| Data layer | `data/scenarios.json`, `data/umass_cs250.json`, `data/japan_discrete_math.json` | 10 synthetic scenarios and two curriculum profiles |
| Implementation | `src/schemas.py`, `src/evaluator.py`, `src/critic.py`, `src/main.py` | Deterministic evaluation pipeline |
| Validation | `tests/` | 38 pytest tests covering schemas, citation verification, alignment, and benchmark accuracy |
| Results | `results/benchmark_report.json`, `results/summary.txt` | 100% accuracy on both single-profile alignment (20/20) and paired attribution (10/10) |

---

## 6. What the PoC Implements vs. the Broader Vision

The checkpoint described a broader Agentic AI vision that extends beyond what Sprint One implements. The table below distinguishes the current PoC's capabilities from the future research objectives stated in the checkpoint.

### Implemented in Sprint One

| Capability | Implementation |
|---|---|
| Structured scenario evaluation | 10 synthetic scenarios evaluated against 2 curriculum profiles |
| Design-limitation vs. contextual-assumption attribution | Three-label taxonomy with deterministic rule-based assignment |
| Citation-grounded diagnostic claims | `CitationCritic` verifies every cited identifier |
| Human-reviewable output | `BenchmarkReport` saved to `results/` with full provenance |
| Reproducible benchmark | Pre-specified expected labels, 100% accuracy, all fixtures committed |
| IBM Bob–supported development | Plan, Agent, and Ask modes used throughout Sprint One |

### Broader Vision (Future Research)

| Concept from Checkpoint | Current Status |
|---|---|
| Multi-source evidence (curriculum documents, expert interviews, learner feedback, system performance data) | Sprint One uses synthetic data only; real multi-source analysis is a future objective |
| Live LLM-based reasoning agents | Sprint One uses deterministic rule matching; LLM-based agents are deferred to future sprints |
| Cross-cultural and cross-institutional comparison at scale | Sprint One uses two synthetic profiles; broader comparative studies are future research |
| Integration with real adaptive learning systems | Sprint One is a standalone evaluator; integration is a future objective |
| Empirically validated curriculum profiles | Sprint One profiles are synthetic; validation with educators is a future objective |

This separation reflects the checkpoint's own framing: Sprint One is "a small proof of concept using structured scenarios" that demonstrates the feasibility of the approach. It is a foundation, not a complete system.

---

## Related Documents

- [IBM Mid-Program Milestone Checkpoint (PDF)](IBM_MidProgram_CheckPoint_Sumary.pdf) — Original historical artifact
- [Problem and Solution Statement](problem_solution.md) — Research question and solution framing
- [Research Methodology](methodology.md) — Benchmark design and evaluation procedure
- [Code Architecture](architecture.md) — Four-step pipeline and module descriptions
- [IBM Bob Technology Statement](technology_statement.md) — Role of IBM Bob and design decisions
- [Data Dictionary](data_dictionary.md) — Field definitions, data types, and validation rules
