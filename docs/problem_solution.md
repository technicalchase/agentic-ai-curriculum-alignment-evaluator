# Problem and Solution Statement

## The Problem

Education prepares students for the future. It is more than completing assignments or passing examinations for a grade. Students gain the knowledge, skills, and confidence to succeed beyond the classroom. As AI becomes part of teaching and learning, a question arises: what happens when feedback does not reflect what students are being taught or what they need to learn?

A student may have a **learning gap** (a concept that was never covered) or a **learning lapse** (a concept that was covered but misapplied). AI feedback that fails to recognize these differences may reinforce misunderstandings rather than address them. The challenge goes beyond determining whether an answer is right or wrong. We need to examine curriculum expectations, prerequisites, and learning objectives. Otherwise, there is no basis for determining whether AI feedback supports student learning or creates additional barriers.

Prior research raises concerns about AI learning systems built around narrow educational assumptions (Woolf et al., 2013). Work with Reusable Learning Objects in COMPSCI 250 identified limits in automated correctness checking, including a lack of personalized explanations, differences in prerequisite knowledge, and the need for human oversight (Randall, 2024; Randall et al., 2025). Research on privacy, fairness, and utility tradeoffs shows that improving one system measure does not necessarily improve every outcome (Randall et al., 2026).

## The Research Question

> When an AI learning system fails a learner, are we questioning the learner or questioning the system?

## The Solution

This Sprint One POC builds a small, fully reproducible Python tool that takes synthetic AI-generated feedback on a standard discrete mathematics exercise and checks it against two institutional curriculum profiles. The tool does not grade students or establish actual causes of a system failure. Instead, it surfaces possible explanations for human review.

The key insight is that the **same feedback** can be appropriate in one curriculum context and inappropriate in another. By comparing two profiles, the evaluator can distinguish between:

- **System design limitations** — feedback that fails (or succeeds) regardless of which curriculum is applied, suggesting a problem in the AI system itself.
- **Contextual assumptions** — feedback that works in one curriculum but not another, suggesting the AI was implicitly designed for a specific educational context.

## Scope Boundaries

- Uses synthetic feedback and synthetic curriculum profiles only. No real student data.
- The Japan profile is fictional and does not represent any actual Japanese institution.
- The system does not send feedback to students and does not establish causal claims.
- Results are for researcher and educator review only.
