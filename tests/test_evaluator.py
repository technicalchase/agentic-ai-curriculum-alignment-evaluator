"""
test_evaluator.py — Unit and integration tests for AlignmentEngine and PairedComparisonEngine.

Verifies that:
  - AlignmentEngine produces valid EvaluationResult objects for every scenario.
  - Citation verification passes on all produced results.
  - PairedComparisonEngine assigns a valid AttributionLabel for every scenario.
  - Cross-profile differences are detected.
  - The evaluator correctly handles self-contradictory feedback (design limitation).
"""
from __future__ import annotations

import pytest

from schemas import (
    AlignmentStatus,
    AttributionLabel,
    DiagnosticClaim,
    EvaluationResult,
    FeedbackScenario,
)
from evaluator import AlignmentEngine, PairedComparisonEngine
from critic import CitationCritic


class TestAlignmentEngine:
    def test_produces_evaluation_result_for_all_scenarios(self, umass_profile, all_scenarios):
        engine = AlignmentEngine(umass_profile)
        for sc in all_scenarios:
            result = engine.evaluate(sc)
            assert isinstance(result, EvaluationResult)
            assert result.scenario_id == sc.scenario_id
            assert result.profile_id == umass_profile.profile_id

    def test_all_claims_have_valid_citations_umass(self, umass_profile, all_scenarios):
        engine = AlignmentEngine(umass_profile)
        for sc in all_scenarios:
            result = engine.evaluate(sc)
            critic = CitationCritic(umass_profile, sc)
            is_valid, bad = critic.check_claims(result.claims)
            assert is_valid, (
                f"Scenario {sc.scenario_id} UMass produced invalid citations: {bad}"
            )

    def test_all_claims_have_valid_citations_japan(self, japan_profile, all_scenarios):
        engine = AlignmentEngine(japan_profile)
        for sc in all_scenarios:
            result = engine.evaluate(sc)
            critic = CitationCritic(japan_profile, sc)
            is_valid, bad = critic.check_claims(result.claims)
            assert is_valid, (
                f"Scenario {sc.scenario_id} Japan produced invalid citations: {bad}"
            )

    def test_retry_count_in_valid_range(self, umass_profile, all_scenarios):
        engine = AlignmentEngine(umass_profile)
        for sc in all_scenarios:
            result = engine.evaluate(sc)
            assert 0 <= result.retry_count <= AlignmentEngine.MAX_RETRIES

    def test_self_contradictory_feedback_misaligned_umass(self, umass_profile):
        """EE_S06 has self-contradictory feedback — both profiles must flag Misaligned."""
        engine = AlignmentEngine(umass_profile)
        sc = _scenario_by_id("EE_S06")
        result = engine.evaluate(sc)
        assert result.alignment_status == AlignmentStatus.MISALIGNED

    def test_self_contradictory_feedback_misaligned_japan(self, japan_profile):
        """EE_S06 — Japan profile must also flag Misaligned."""
        engine = AlignmentEngine(japan_profile)
        sc = _scenario_by_id("EE_S06")
        result = engine.evaluate(sc)
        assert result.alignment_status == AlignmentStatus.MISALIGNED

    def test_cross_profile_difference_exists(self, umass_profile, japan_profile, all_scenarios):
        """At least one scenario must produce different alignment status across profiles."""
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        found_difference = False
        for sc in all_scenarios:
            u = umass_engine.evaluate(sc)
            j = japan_engine.evaluate(sc)
            if u.alignment_status != j.alignment_status:
                found_difference = True
                break
        assert found_difference, "No cross-profile difference detected — acceptance criterion not met"

    def test_each_result_has_at_least_one_claim(self, umass_profile, all_scenarios):
        engine = AlignmentEngine(umass_profile)
        for sc in all_scenarios:
            result = engine.evaluate(sc)
            assert len(result.claims) >= 1, (
                f"Scenario {sc.scenario_id} produced no claims"
            )


class TestPairedComparisonEngine:
    def test_produces_paired_result_for_all_scenarios(self, umass_profile, japan_profile, all_scenarios):
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        paired_engine = PairedComparisonEngine()

        for sc in all_scenarios:
            u = umass_engine.evaluate(sc)
            j = japan_engine.evaluate(sc)
            pr = paired_engine.compare(sc, u, j)
            assert pr.scenario_id == sc.scenario_id
            assert isinstance(pr.paired_attribution_label, AttributionLabel)
            assert len(pr.paired_rationale) > 0

    def test_both_misaligned_gives_design_limitation(self, umass_profile, japan_profile):
        """EE_S06 — both misaligned → Consistent_With_Design_Limitation."""
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        paired_engine = PairedComparisonEngine()
        sc = _scenario_by_id("EE_S06")
        u = umass_engine.evaluate(sc)
        j = japan_engine.evaluate(sc)
        pr = paired_engine.compare(sc, u, j)
        assert pr.paired_attribution_label == AttributionLabel.DESIGN_LIMITATION

    def test_different_alignment_gives_contextual_assumption(self, umass_profile, japan_profile, all_scenarios):
        """
        Any scenario where profiles differ in alignment status should produce
        Consistent_With_Contextual_Assumption.
        """
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        paired_engine = PairedComparisonEngine()

        for sc in all_scenarios:
            u = umass_engine.evaluate(sc)
            j = japan_engine.evaluate(sc)
            if u.alignment_status != j.alignment_status:
                pr = paired_engine.compare(sc, u, j)
                assert pr.paired_attribution_label == AttributionLabel.CONTEXTUAL_ASSUMPTION, (
                    f"{sc.scenario_id}: profiles differ but got {pr.paired_attribution_label}"
                )


# ---------------------------------------------------------------------------
# Benchmark accuracy tests
# ---------------------------------------------------------------------------

class TestBenchmarkAccuracy:
    """
    Integration tests that check the evaluator meets the Sprint One acceptance
    criteria against the predefined ground-truth labels.
    """

    def _run_all(self, umass_profile, japan_profile, all_scenarios):
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        paired_engine = PairedComparisonEngine()
        paired_results = []
        for sc in all_scenarios:
            u = umass_engine.evaluate(sc)
            j = japan_engine.evaluate(sc)
            paired_results.append(paired_engine.compare(sc, u, j))
        return paired_results

    def test_single_profile_accuracy_meets_80_percent(self, umass_profile, japan_profile, all_scenarios):
        paired_results = self._run_all(umass_profile, japan_profile, all_scenarios)
        scenario_map = {s.scenario_id: s for s in all_scenarios}
        correct = 0
        total   = 0
        for pr in paired_results:
            sc = scenario_map[pr.scenario_id]
            total += 2
            if pr.umass_result.alignment_status == sc.expected_umass_alignment:
                correct += 1
            if pr.japan_result.alignment_status == sc.expected_japan_alignment:
                correct += 1
        accuracy = correct / total
        assert accuracy >= 0.80, (
            f"Single-profile accuracy {correct}/{total} = {accuracy:.1%} < 80% target"
        )

    def test_paired_attribution_accuracy_meets_80_percent(self, umass_profile, japan_profile, all_scenarios):
        paired_results = self._run_all(umass_profile, japan_profile, all_scenarios)
        scenario_map = {s.scenario_id: s for s in all_scenarios}
        correct = sum(
            1 for pr in paired_results
            if pr.paired_attribution_label == scenario_map[pr.scenario_id].expected_attribution
        )
        total   = len(paired_results)
        accuracy = correct / total
        assert accuracy >= 0.80, (
            f"Paired attribution accuracy {correct}/{total} = {accuracy:.1%} < 80% target"
        )

    def test_negative_controls_no_cross_profile_difference(self, umass_profile, japan_profile, all_scenarios):
        """
        Negative control scenarios must NOT produce different alignment outcomes
        across profiles — both should agree on the same alignment status.
        """
        umass_engine = AlignmentEngine(umass_profile)
        japan_engine = AlignmentEngine(japan_profile)
        failures = []
        for sc in all_scenarios:
            if not sc.is_negative_control:
                continue
            u = umass_engine.evaluate(sc)
            j = japan_engine.evaluate(sc)
            if u.alignment_status != j.alignment_status:
                failures.append(
                    f"{sc.scenario_id}: UMass={u.alignment_status.value}, Japan={j.alignment_status.value}"
                )
        assert not failures, (
            "Negative control scenarios showed unexpected cross-profile differences:\n"
            + "\n".join(failures)
        )


# ---------------------------------------------------------------------------
# Helper — build a lightweight scenario for specific unit tests
# ---------------------------------------------------------------------------

def _scenario_by_id(scenario_id: str) -> FeedbackScenario:
    """Load a single scenario by ID directly from fixtures."""
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    for item in raw:
        if item.get("scenario_id") == scenario_id:
            clean = {k: v for k, v in item.items() if not k.startswith("_")}
            return FeedbackScenario.model_validate(clean)
    raise KeyError(f"Scenario {scenario_id!r} not found in fixtures.")
