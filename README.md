# agentic-ai-curriculum-alignment-evaluator

Agentic AI proof of concept (POC) developed using IBM Bob to evaluate AI generated educational feedback against different curriculum expectations. Using 10 synthetic scenarios and two curriculum profiles, the POC examines whether feedback supports learning, identifies possible gaps in system design, and provides evidence for human review.

## Research Overview

Education prepares students for the future. As AI becomes part of teaching and learning, students and educators increasingly rely on AI generated feedback. But what happens when that feedback does not match what students are taught?

A learning gap may reflect missing knowledge or skills. A learning lapse may reflect a temporary breakdown in understanding. However, the problem may also come from the AI system itself.

These challenges affect more than students. Educators need feedback that supports their teaching goals. Institutions need systems that reflect their curriculum expectations. Researchers and developers need ways to identify where AI systems fall short.

This proof of concept (POC) examines these challenges through synthetic scenarios and different curriculum expectations. It focuses on identifying possible gaps between AI generated feedback and what students are expected to learn.

**Core Research Question**

When an AI learning system fails a learner, are we questioning the learner or questioning the system?

## Technical Overview

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

## Experimental Framework

This POC examines how AI generated educational feedback aligns with different curriculum expectations. It uses synthetic data to test the system without collecting student information.

The evaluation includes:

- **10 synthetic scenarios:** Examples of AI generated feedback used for testing.
- **Two curriculum profiles:** Different institutional expectations used to evaluate the same feedback.
- **20 institutional evaluations:** Each scenario is evaluated against both curriculum profiles.
- **10 paired comparisons:** Results are compared to identify differences in feedback alignment.
- **Evidence verification:** The system checks whether its findings are supported by the curriculum profiles.

The POC uses an 80% accuracy target for its evaluation measures. The results help identify where AI feedback aligns with curriculum expectations and where differences may occur.

The experiments provide a starting point for further research. They do not measure actual student learning outcomes.


## System Architecture

The POC uses an Agentic AI framework to evaluate educational feedback against different curriculum expectations.

The system includes:

- **Input Data:** Synthetic scenarios and two curriculum profiles.
- **Data Validation:** Checks that the information follows the required format.
- **Feedback Evaluator:** Examines how AI generated feedback aligns with each curriculum.
- **Evidence Checker:** Checks whether the evaluation is supported by the curriculum information.
- **Paired Comparison:** Compares results across the two curriculum profiles.
- **Evaluation Results:** Records findings for human review.

### Architecture Diagram

The diagram below shows how the different parts of the system work together.

See the [Code Architecture](docs/architecture.md) document for the architecture diagram and a description of each component.

### Data Dictionary

The [Data Dictionary](docs/data_dictionary.md) explains the information used by the system. It includes field definitions, data types, and validation rules.

IBM Bob supports the development and testing of the system based on this framework.


## IBM Bob Development and Support

This POC is developed through the IBM SkillsBuild AI Experiential Learning Lab using IBM Bob as the primary AI development tool.

IBM Bob supports the project through its software development capabilities:

- **Plan Mode:** Helps organize the system design and development steps.
- **Agent Mode:** Supports Python code generation, testing, and debugging.
- **Ask Mode:** Helps explain code and answer technical questions.
- **Documentation:** Supports the development of clear technical documents.
- **Code Review:** Helps identify errors and improve the implementation.

### IBM Bob's Value

IBM Bob helps turn the research framework into a working POC. It supports the development of the curriculum alignment evaluator while allowing the researcher to focus on the research questions, evaluation methods, and findings.

The IBM SkillsBuild AI Experiential Learning Lab provides an opportunity to apply AI development tools to a real research problem. This project demonstrates how IBM Bob supports research, software development, and practical solutions to challenges in education.

For more information, see the [IBM Bob IDE Documentation](https://bob.ibm.com/docs/ide).

## Related Publications

This POC builds on my previous research in AI in Education, adaptive feedback, software engineering, and responsible AI.

My six peer reviewed publications provide background for the research framework. Each examines a challenge that helps explain why we need to evaluate AI systems and not just their users.

The publications address:

- **Scholarly Literature:** Researchers need reliable ways to find and review existing knowledge. AI tools may miss important context or overlook different perspectives. This POC examines a similar problem when AI feedback overlooks curriculum expectations.

- **Neural Networks:** Neural networks can make decisions without clearly explaining why. This makes it difficult to identify errors or understand system behavior. The POC examines similar challenges when AI generated feedback does not match curriculum expectations.

- **Neuro-evolution and Robustness:** An AI system may perform well in one setting but struggle when conditions change. This raises questions about system reliability. The POC examines whether the same feedback remains appropriate across different curriculum expectations.

- **Privacy, Fairness, and Utility:** Improving one part of an AI system may create problems elsewhere. These tradeoffs raise questions about whose needs the system serves. The POC examines how curriculum differences may affect the fairness and usefulness of AI feedback.

- **Adaptive Feedback and Student Engagement:** Feedback that does not reflect a student's learning needs may create confusion or reduce engagement. The POC examines whether AI generated feedback supports what students are expected to learn.
 
- **AI in Education and Automata Theory:** AI learning systems may follow rules and assumptions that do not reflect how students are taught. This raises questions about whether a learning gap comes from the student or the system. My synthesis paper brings AI in Education and Automata Theory together to examine these challenges. The paper supported my Ph.D. candidacy application. Professors Beverly Woolf and David A. Mix Barrington served as readers and later joined my dissertation committee. This POC extends that research by examining AI generated feedback across different curriculum expectations.

See [Related Publications](docs/related_publications.md) for publication titles, references, and links.

Together, these publications help connect the POC to my broader research and dissertation. They raise a common question: When an AI system falls short, are we examining the limitations of the system or placing the burden on the user?


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
