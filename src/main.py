"""
main.py — Sprint One POC pipeline runner.

Implements the full four-step evaluation pipeline:

  1. Load and validate inputs (Pydantic)
  2. Evaluate each scenario against each institutional profile (20 runs)
  3. Perform citation verification with up to 2 retries
  4. Produce 10 paired comparisons and score against predefined expected labels
  5. Save results to results/ and print a human-readable summary

Usage
-----
    python src/main.py

All paths are resolved relative to the repository root so the script can be
run from any directory.

No external API calls are made.  The pipeline is fully deterministic.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — make src/ importable when invoked from repository root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR   = REPO_ROOT / "src"
DATA_DIR  = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure stdout/stderr handle unicode on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from evaluator import AlignmentEngine, PairedComparisonEngine
from schemas import (
    AlignmentStatus,
    AttributionLabel,
    BenchmarkReport,
    FeedbackScenario,
    InstitutionalProfile,
    PairedAttributionResult,
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_profile(path: Path) -> InstitutionalProfile:
    """Load and validate an institutional profile JSON file."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return InstitutionalProfile.model_validate(data)


def load_scenarios(path: Path) -> list[FeedbackScenario]:
    """Load and validate all feedback scenarios from a JSON array file."""
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    scenarios = []
    for item in raw:
        # Strip internal _notes keys before validation (documentation only)
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        scenarios.append(FeedbackScenario.model_validate(clean))
    return scenarios


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def score_single_profile(
    paired_results: list[PairedAttributionResult],
    scenarios: list[FeedbackScenario],
) -> tuple[int, int]:
    """
    Count correct single-profile alignment decisions (N = 20).

    For each scenario we check:
      - umass_result.alignment_status == scenario.expected_umass_alignment
      - japan_result.alignment_status == scenario.expected_japan_alignment
    """
    scenario_map = {s.scenario_id: s for s in scenarios}
    correct = 0
    total   = 0

    for pr in paired_results:
        sc = scenario_map[pr.scenario_id]
        total += 2  # one for each profile
        if pr.umass_result.alignment_status == sc.expected_umass_alignment:
            correct += 1
        if pr.japan_result.alignment_status == sc.expected_japan_alignment:
            correct += 1

    return correct, total


def score_paired_attribution(
    paired_results: list[PairedAttributionResult],
    scenarios: list[FeedbackScenario],
) -> tuple[int, int]:
    """Count correct paired attribution decisions (N = 10)."""
    scenario_map = {s.scenario_id: s for s in scenarios}
    correct = 0
    total   = len(paired_results)

    for pr in paired_results:
        sc = scenario_map[pr.scenario_id]
        if pr.paired_attribution_label == sc.expected_attribution:
            correct += 1

    return correct, total


def has_cross_profile_difference(paired_results: list[PairedAttributionResult]) -> bool:
    """Return True if at least one scenario has different alignment outcomes across profiles."""
    for pr in paired_results:
        if pr.umass_result.alignment_status != pr.japan_result.alignment_status:
            return True
    return False


def all_citations_valid(paired_results: list[PairedAttributionResult]) -> bool:
    """Return True when no result was downgraded due to citation failure."""
    ii = AlignmentStatus.INSUFFICIENT_INFORMATION
    for pr in paired_results:
        # Insufficient_Information triggered by citation failure (not by ambiguity)
        u = pr.umass_result
        j = pr.japan_result
        if u.alignment_status == ii and u.retry_count == AlignmentEngine.MAX_RETRIES:
            return False
        if j.alignment_status == ii and j.retry_count == AlignmentEngine.MAX_RETRIES:
            return False
    return True


def negative_control_summary(
    paired_results: list[PairedAttributionResult],
    scenarios: list[FeedbackScenario],
) -> str:
    """Summarise evaluator performance on negative control scenarios."""
    neg_scenarios = [s for s in scenarios if s.is_negative_control]
    lines = []
    scenario_map = {s.scenario_id: s for s in scenarios}

    for sid in [s.scenario_id for s in neg_scenarios]:
        pr = next((p for p in paired_results if p.scenario_id == sid), None)
        if pr is None:
            continue
        sc = scenario_map[sid]
        u_ok = pr.umass_result.alignment_status == sc.expected_umass_alignment
        j_ok = pr.japan_result.alignment_status == sc.expected_japan_alignment
        lines.append(
            f"  {sid}: UMass {'✓' if u_ok else '✗'} "
            f"(got {pr.umass_result.alignment_status.value}, "
            f"expected {sc.expected_umass_alignment.value})  |  "
            f"Japan {'✓' if j_ok else '✗'} "
            f"(got {pr.japan_result.alignment_status.value}, "
            f"expected {sc.expected_japan_alignment.value})"
        )
    return "\n".join(lines) if lines else "No negative controls found."


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline() -> BenchmarkReport:
    """Execute the full Sprint One evaluation pipeline."""

    RESULTS_DIR.mkdir(exist_ok=True)

    # --- Step 1: Load and validate inputs ---
    print("Loading curriculum profiles …")
    umass_profile = load_profile(DATA_DIR / "umass_cs250.json")
    japan_profile = load_profile(DATA_DIR / "japan_discrete_math.json")
    print(f"  ✓ {umass_profile.profile_id}")
    print(f"  ✓ {japan_profile.profile_id}")

    print("Loading feedback scenarios …")
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")
    print(f"  ✓ {len(scenarios)} scenarios loaded")

    # --- Steps 2–3: Evaluate each scenario against each profile ---
    umass_engine = AlignmentEngine(umass_profile)
    japan_engine = AlignmentEngine(japan_profile)
    paired_engine = PairedComparisonEngine()

    print("\nRunning evaluations …")
    paired_results: list[PairedAttributionResult] = []

    for sc in scenarios:
        umass_result = umass_engine.evaluate(sc)
        japan_result = japan_engine.evaluate(sc)

        # --- Step 4: Paired comparison ---
        paired = paired_engine.compare(sc, umass_result, japan_result)
        paired_results.append(paired)

        u_status = umass_result.alignment_status.value
        j_status = japan_result.alignment_status.value
        label    = paired.paired_attribution_label.value
        print(f"  {sc.scenario_id}: UMass={u_status:<27} Japan={j_status:<27} → {label}")

    # --- Scoring ---
    sp_correct, sp_total = score_single_profile(paired_results, scenarios)
    pa_correct, pa_total = score_paired_attribution(paired_results, scenarios)
    sp_accuracy = sp_correct / sp_total if sp_total else 0.0
    pa_accuracy = pa_correct / pa_total if pa_total else 0.0

    neg_summary = negative_control_summary(paired_results, scenarios)
    cross_diff  = has_cross_profile_difference(paired_results)
    cites_ok    = all_citations_valid(paired_results)

    report = BenchmarkReport(
        paired_results=paired_results,
        single_profile_correct=sp_correct,
        single_profile_total=sp_total,
        single_profile_accuracy=round(sp_accuracy, 4),
        paired_attribution_correct=pa_correct,
        paired_attribution_total=pa_total,
        paired_attribution_accuracy=round(pa_accuracy, 4),
        negative_control_summary=neg_summary,
        single_profile_target_met=(sp_correct >= 16),
        paired_attribution_target_met=(pa_correct >= 8),
        cross_profile_difference_found=cross_diff,
        all_citations_valid=cites_ok,
    )

    # --- Save results ---
    report_path = RESULTS_DIR / "benchmark_report.json"
    with report_path.open("w", encoding="utf-8") as fh:
        fh.write(report.model_dump_json(indent=2))
    print(f"\nReport saved → {report_path}")

    # --- Save readable summary ---
    summary_path = RESULTS_DIR / "summary.txt"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write(format_summary(report, scenarios, paired_results))
    print(f"Summary saved → {summary_path}")

    return report


# ---------------------------------------------------------------------------
# Human-readable summary formatter
# ---------------------------------------------------------------------------

def format_summary(
    report: BenchmarkReport,
    scenarios: list[FeedbackScenario],
    paired_results: list[PairedAttributionResult],
) -> str:
    scenario_map = {s.scenario_id: s for s in scenarios}
    lines = []
    lines.append("=" * 72)
    lines.append("SPRINT ONE POC — BENCHMARK RESULTS SUMMARY")
    lines.append("Agentic AI Curriculum Alignment Evaluator")
    lines.append("=" * 72)
    lines.append("")

    # --- Acceptance criteria ---
    lines.append("ACCEPTANCE CRITERIA")
    lines.append("-" * 40)

    sp_pct = round(report.single_profile_accuracy * 100, 1)
    pa_pct = round(report.paired_attribution_accuracy * 100, 1)

    sp_pass = "✓ PASS" if report.single_profile_target_met else "✗ FAIL"
    pa_pass = "✓ PASS" if report.paired_attribution_target_met else "✗ FAIL"
    cp_pass = "✓ PASS" if report.cross_profile_difference_found else "✗ FAIL"
    ci_pass = "✓ PASS" if report.all_citations_valid else "✗ FAIL"

    lines.append(f"Single-profile alignment accuracy  (N=20): {report.single_profile_correct}/{report.single_profile_total} = {sp_pct}%  [target ≥80%]  {sp_pass}")
    lines.append(f"Paired attribution accuracy        (N=10): {report.paired_attribution_correct}/{report.paired_attribution_total} = {pa_pct}%  [target ≥80%]  {pa_pass}")
    lines.append(f"Cross-profile difference found            :                              {cp_pass}")
    lines.append(f"All citations valid                        :                              {ci_pass}")
    lines.append("")

    # --- Negative controls ---
    lines.append("NEGATIVE CONTROL PERFORMANCE")
    lines.append("-" * 40)
    lines.append(report.negative_control_summary)
    lines.append("")

    # --- Per-scenario detail ---
    lines.append("PER-SCENARIO DETAIL")
    lines.append("-" * 72)
    header = f"{'Scenario':<10} {'UMass Got':<26} {'Japan Got':<26} {'Attribution':<38} {'SP✓' }"
    lines.append(header)
    lines.append("-" * 72)

    for pr in paired_results:
        sc = scenario_map[pr.scenario_id]
        u_got = pr.umass_result.alignment_status.value
        j_got = pr.japan_result.alignment_status.value
        attr  = pr.paired_attribution_label.value

        u_ok = "✓" if pr.umass_result.alignment_status == sc.expected_umass_alignment else "✗"
        j_ok = "✓" if pr.japan_result.alignment_status == sc.expected_japan_alignment else "✗"
        a_ok = "✓" if pr.paired_attribution_label == sc.expected_attribution else "✗"
        nc   = " [NEG CTRL]" if sc.is_negative_control else ""

        lines.append(f"{pr.scenario_id:<10} {u_got+' '+u_ok:<26} {j_got+' '+j_ok:<26} {attr+' '+a_ok:<38}{nc}")

    lines.append("")

    # --- Error analysis ---
    sp_errors = []
    pa_errors = []
    ii_cases  = []

    for pr in paired_results:
        sc = scenario_map[pr.scenario_id]
        if pr.umass_result.alignment_status != sc.expected_umass_alignment:
            sp_errors.append(f"  {pr.scenario_id} UMass: got {pr.umass_result.alignment_status.value}, expected {sc.expected_umass_alignment.value}")
        if pr.japan_result.alignment_status != sc.expected_japan_alignment:
            sp_errors.append(f"  {pr.scenario_id} Japan: got {pr.japan_result.alignment_status.value}, expected {sc.expected_japan_alignment.value}")
        if pr.paired_attribution_label != sc.expected_attribution:
            pa_errors.append(f"  {pr.scenario_id}: got {pr.paired_attribution_label.value}, expected {sc.expected_attribution.value}")
        if pr.umass_result.alignment_status == AlignmentStatus.INSUFFICIENT_INFORMATION:
            ii_cases.append(f"  {pr.scenario_id} UMass (retries={pr.umass_result.retry_count})")
        if pr.japan_result.alignment_status == AlignmentStatus.INSUFFICIENT_INFORMATION:
            ii_cases.append(f"  {pr.scenario_id} Japan (retries={pr.japan_result.retry_count})")

    lines.append("ERROR ANALYSIS")
    lines.append("-" * 40)
    if sp_errors:
        lines.append("Single-profile misclassifications:")
        lines.extend(sp_errors)
    else:
        lines.append("Single-profile misclassifications: none")

    if pa_errors:
        lines.append("Paired attribution misclassifications:")
        lines.extend(pa_errors)
    else:
        lines.append("Paired attribution misclassifications: none")

    if ii_cases:
        lines.append("Insufficient_Information outcomes:")
        lines.extend(ii_cases)
    else:
        lines.append("Insufficient_Information outcomes: none")

    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF REPORT")
    lines.append("=" * 72)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    report = run_pipeline()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    sp_pct = round(report.single_profile_accuracy * 100, 1)
    pa_pct = round(report.paired_attribution_accuracy * 100, 1)
    print(f"Single-profile alignment (N=20): {report.single_profile_correct}/{report.single_profile_total} = {sp_pct}%  {'✓ PASS' if report.single_profile_target_met else '✗ FAIL'}")
    print(f"Paired attribution       (N=10): {report.paired_attribution_correct}/{report.paired_attribution_total} = {pa_pct}%  {'✓ PASS' if report.paired_attribution_target_met else '✗ FAIL'}")
    print(f"Cross-profile difference found : {report.cross_profile_difference_found}")
    print(f"All citations valid             : {report.all_citations_valid}")
