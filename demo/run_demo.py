#!/usr/bin/env python3
"""
run_demo.py — Interactive demonstration of the Curriculum Alignment Evaluator POC.

Demonstrates:
  1. One institutional curriculum alignment evaluation (EE_S05 against UMass CS250)
  2. One paired curriculum comparison (EE_S03: UMass vs Japan)
  3. Automated test suite results

Run from the repository root:
    python demo/run_demo.py

No API keys or internet access required — all evaluation logic is deterministic.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import fill, indent

# ---------------------------------------------------------------------------
# Path setup — make src/ importable when invoked from repository root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR   = REPO_ROOT / "src"
DATA_DIR  = REPO_ROOT / "data"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure stdout/stderr handle unicode on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json

from evaluator import AlignmentEngine, PairedComparisonEngine
from schemas import FeedbackScenario, InstitutionalProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_profile(name: str) -> InstitutionalProfile:
    path = DATA_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return InstitutionalProfile.model_validate(data)


def _load_scenario(scenario_id: str) -> FeedbackScenario:
    path = DATA_DIR / "scenarios.json"
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    for item in raw:
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        sc = FeedbackScenario.model_validate(clean)
        if sc.scenario_id == scenario_id:
            return sc
    raise KeyError(f"Scenario '{scenario_id}' not found in scenarios.json")


def _hr(char: str = "=", width: int = 72) -> None:
    print(char * width)


def _section(title: str) -> None:
    print()
    _hr()
    print(f"  {title}")
    _hr()


def _wrap(text: str, prefix: str = "  ") -> None:
    for paragraph in text.split("\n"):
        if paragraph.strip():
            print(fill(paragraph.strip(), width=70, initial_indent=prefix,
                       subsequent_indent=prefix))
        else:
            print()


def _print_evaluation_result(result, scenario: FeedbackScenario,
                              profile: InstitutionalProfile) -> None:
    status      = result.alignment_status.value
    retry_info  = f"  (citation retries: {result.retry_count})" if result.retry_count else ""
    expected    = (scenario.expected_umass_alignment
                   if profile.profile_id == "umass_cs250"
                   else scenario.expected_japan_alignment)
    match_sym   = "✓" if result.alignment_status == expected else "✗"

    print(f"  Profile       : {profile.profile_id}  ({profile.institution_name})")
    print(f"  Bloom target  : {profile.bloom_baseline_level.value}")
    print(f"  Status        : {status}  {match_sym} (expected: {expected.value}){retry_info}")
    print()
    print("  Supporting evidence (DiagnosticClaims):")
    for i, claim in enumerate(result.claims, 1):
        cited = ", ".join(claim.cited_ids)
        print(f"  [{i}] cited: {cited}")
        _wrap(claim.claim_text, prefix="      ")
        print()


# ---------------------------------------------------------------------------
# Demo 1 — Single institutional alignment evaluation
# ---------------------------------------------------------------------------

def demo_single_alignment() -> None:
    _section("DEMO 1 — Single Institutional Curriculum Alignment Evaluation")

    # EE_S05: student has a near-correct answer; feedback demands a formal
    # inductive proof.  UMass expects this (Aligned); Japan does not (Misaligned).
    # We show UMass here as the single-profile demonstration.
    scenario_id = "EE_S05"
    profile     = _load_profile("umass_cs250")
    scenario    = _load_scenario(scenario_id)
    engine      = AlignmentEngine(profile)
    result      = engine.evaluate(scenario)

    print(f"\n  Scenario      : {scenario.scenario_id}")
    print(f"  Student attempt:")
    print(f"      {scenario.student_attempt}")
    print(f"\n  AI feedback (held constant across profiles):")
    _wrap(scenario.ai_feedback_text)
    print()
    _print_evaluation_result(result, scenario, profile)

    print("  ► The feedback demands a formal inductive proof, which is a")
    print("    required justification standard at UMass COMPSCI 250 (SR02, SR04).")
    print("    Result: ALIGNED with UMass expectations.")


# ---------------------------------------------------------------------------
# Demo 2 — Paired curriculum comparison
# ---------------------------------------------------------------------------

def demo_paired_comparison() -> None:
    _section("DEMO 2 — Paired Curriculum Comparison (UMass vs Japan)")

    # EE_S03: student submits (a*b*)* — wrong.  Feedback advises drawing a
    # 4-state DFA and using state-elimination.  DFA is in-scope at UMass
    # (Aligned) but explicitly out-of-scope at the Japan profile (Misaligned).
    scenario_id  = "EE_S03"
    umass_profile = _load_profile("umass_cs250")
    japan_profile = _load_profile("japan_discrete_math")
    scenario      = _load_scenario(scenario_id)

    umass_engine = AlignmentEngine(umass_profile)
    japan_engine = AlignmentEngine(japan_profile)
    paired_engine = PairedComparisonEngine()

    umass_result = umass_engine.evaluate(scenario)
    japan_result = japan_engine.evaluate(scenario)
    paired       = paired_engine.compare(scenario, umass_result, japan_result)

    print(f"\n  Scenario      : {scenario.scenario_id}")
    print(f"  Student attempt:")
    print(f"      {scenario.student_attempt}")
    print(f"\n  AI feedback (identical for both profiles):")
    _wrap(scenario.ai_feedback_text)
    print()

    print("  --- UMass COMPSCI 250 evaluation ---")
    _print_evaluation_result(umass_result, scenario, umass_profile)

    print("  --- Japan Discrete Mathematics evaluation ---")
    _print_evaluation_result(japan_result, scenario, japan_profile)

    exp_label   = scenario.expected_attribution
    label_match = "✓" if paired.paired_attribution_label == exp_label else "✗"
    print("  --- Paired attribution ---")
    print(f"  Label    : {paired.paired_attribution_label.value}  "
          f"{label_match} (expected: {exp_label.value})")
    print(f"  Rationale:")
    _wrap(paired.paired_rationale)
    print()
    print("  ► The same feedback aligns with UMass (DFA is prerequisite knowledge)")
    print("    but misaligns with Japan (DFA is explicitly out-of-scope here).")
    print("    Result: Consistent_With_Contextual_Assumption")


# ---------------------------------------------------------------------------
# Demo 3 — Automated test suite
# ---------------------------------------------------------------------------

def demo_run_tests() -> None:
    _section("DEMO 3 — Automated Test Suite")

    print("\n  Running: python -m pytest tests/ -v\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    print()
    if result.returncode == 0:
        print("  ✓ All tests passed.")
    else:
        print(f"  ✗ Test run exited with code {result.returncode}.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _hr()
    print("  Curriculum Alignment Evaluator — Sprint One POC Demo")
    print("  Agentic AI · IBM SkillsBuild · Deterministic Rule-Based Pipeline")
    _hr()

    demo_single_alignment()
    demo_paired_comparison()
    demo_run_tests()

    print()
    _hr()
    print("  Demo complete.")
    print("  Full benchmark: python src/main.py")
    print("  Results saved to: results/benchmark_report.json, results/summary.txt")
    _hr()
    print()
