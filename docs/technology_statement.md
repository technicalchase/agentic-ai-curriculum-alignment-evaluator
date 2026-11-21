# IBM Bob Technology Statement

## Role of IBM Bob

This POC was developed using IBM Bob as the primary development environment. IBM Bob served as an Agentic AI coding assistant throughout the Sprint One implementation, supporting:

- **Architecture design** — iterative discussion of the pipeline structure and schema design against the Technical Charter requirements.
- **Code generation** — initial drafts of `schemas.py`, `evaluator.py`, `critic.py`, and `main.py`.
- **Debugging** — identifying and correcting logic errors in the alignment engine through structured analysis of benchmark failures.
- **Documentation** — populating the documentation stubs with content derived from the Technical Charter.
- **Test design** — generating the pytest test suite and verifying that all 38 tests pass.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Data validation | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| Testing | [pytest](https://docs.pytest.org/) |
| Data format | JSON |
| Development environment | IBM Bob (VS Code extension) |

## Design Decisions

**No LLM API calls at runtime.** The alignment engine is deterministic rule-based pattern matching. This was a deliberate choice for Sprint One to ensure full reproducibility without requiring API keys or network access. The tradeoff is that the evaluator's logic is explicit but limited to the rules coded into `evaluator.py`.

**Pydantic for all I/O.** Using Pydantic ensures that invalid inputs fail fast with clear error messages rather than propagating silently through the pipeline.

**Citation grounding.** Every diagnostic claim must cite a verifiable `rule_id` or `scenario_id`. This prevents the evaluator from making claims that cannot be traced back to the documented curriculum profile, which is critical for the human review use case.

**Separation of structural and communicative rules.** The `InstitutionalProfile` model keeps `structural_rules` and `socio_communicative_norms` in separate lists. This prevents the evaluator from conflating curriculum-level failures with communication-style preferences.

## Reproducibility

The full pipeline is reproducible without any external dependencies beyond `pydantic` and `pytest`:

```bash
pip install pydantic pytest
python src/main.py
python -m pytest tests/ -v
```

All fixtures, expected labels, and results are committed to the repository.
