"""
test_schemas.py — Unit tests for Pydantic schema validation.

Verifies that:
  - Valid data loads without errors.
  - Invalid data (missing required fields, bad enum values) is rejected.
  - Cross-field validators fire correctly.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import (
    AlignmentStatus,
    AttributionLabel,
    BloomLevel,
    DiagnosticClaim,
    EvaluationResult,
    FeedbackScenario,
    InstitutionalProfile,
    PairedAttributionResult,
    RuleItem,
)


# ---------------------------------------------------------------------------
# RuleItem
# ---------------------------------------------------------------------------

class TestRuleItem:
    def test_valid(self):
        r = RuleItem(rule_id="R01", text="Some rule text.")
        assert r.rule_id == "R01"

    def test_missing_text_rejected(self):
        with pytest.raises(ValidationError):
            RuleItem(rule_id="R01")


# ---------------------------------------------------------------------------
# DiagnosticClaim
# ---------------------------------------------------------------------------

class TestDiagnosticClaim:
    def test_valid(self):
        c = DiagnosticClaim(claim_text="Some claim.", cited_ids=["R01"])
        assert c.cited_ids == ["R01"]

    def test_empty_cited_ids_rejected(self):
        with pytest.raises(ValidationError):
            DiagnosticClaim(claim_text="Some claim.", cited_ids=[])


# ---------------------------------------------------------------------------
# InstitutionalProfile
# ---------------------------------------------------------------------------

class TestInstitutionalProfile:
    def test_loads_from_fixture(self, umass_profile):
        assert umass_profile.profile_id == "umass_cs250"
        assert umass_profile.bloom_baseline_level == BloomLevel.ANALYZE

    def test_all_rule_ids_non_empty(self, umass_profile):
        ids = umass_profile.all_rule_ids()
        assert len(ids) > 0
        assert "umass_SR01" in ids
        assert "umass_SCN01" in ids

    def test_japan_profile_loads(self, japan_profile):
        assert japan_profile.profile_id == "japan_discrete_math"
        assert japan_profile.bloom_baseline_level == BloomLevel.UNDERSTAND

    def test_bad_bloom_level_rejected(self):
        with pytest.raises(ValidationError):
            InstitutionalProfile(
                profile_id="test",
                institution_name="Test",
                structural_rules=[],
                socio_communicative_norms=[],
                bloom_baseline_level="Memorise",  # not a valid level
            )


# ---------------------------------------------------------------------------
# FeedbackScenario
# ---------------------------------------------------------------------------

class TestFeedbackScenario:
    def test_all_scenarios_load(self, all_scenarios):
        assert len(all_scenarios) == 10

    def test_scenario_ids_unique(self, all_scenarios):
        ids = [s.scenario_id for s in all_scenarios]
        assert len(ids) == len(set(ids))

    def test_expected_labels_valid(self, all_scenarios):
        for s in all_scenarios:
            assert isinstance(s.expected_umass_alignment, AlignmentStatus)
            assert isinstance(s.expected_japan_alignment, AlignmentStatus)
            assert isinstance(s.expected_attribution, AttributionLabel)

    def test_negative_controls_present(self, all_scenarios):
        neg_ctrls = [s for s in all_scenarios if s.is_negative_control]
        assert len(neg_ctrls) >= 1, "Benchmark must include at least one negative control"


# ---------------------------------------------------------------------------
# EvaluationResult
# ---------------------------------------------------------------------------

class TestEvaluationResult:
    def test_valid_construction(self):
        r = EvaluationResult(
            scenario_id="EE_S01",
            profile_id="umass_cs250",
            alignment_status=AlignmentStatus.ALIGNED,
            claims=[DiagnosticClaim(claim_text="Test.", cited_ids=["EE_S01"])],
            retry_count=0,
        )
        assert r.alignment_status == AlignmentStatus.ALIGNED

    def test_retry_count_exceeds_max_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationResult(
                scenario_id="EE_S01",
                profile_id="umass_cs250",
                alignment_status=AlignmentStatus.ALIGNED,
                claims=[DiagnosticClaim(claim_text="Test.", cited_ids=["EE_S01"])],
                retry_count=3,  # max is 2
            )


# ---------------------------------------------------------------------------
# PairedAttributionResult
# ---------------------------------------------------------------------------

class TestPairedAttributionResult:
    def _make_eval(self, scenario_id: str, profile_id: str) -> EvaluationResult:
        return EvaluationResult(
            scenario_id=scenario_id,
            profile_id=profile_id,
            alignment_status=AlignmentStatus.ALIGNED,
            claims=[DiagnosticClaim(claim_text="ok", cited_ids=[scenario_id])],
        )

    def test_valid_paired_result(self):
        u = self._make_eval("EE_S01", "umass_cs250")
        j = self._make_eval("EE_S01", "japan_discrete_math")
        pr = PairedAttributionResult(
            scenario_id="EE_S01",
            umass_result=u,
            japan_result=j,
            paired_attribution_label=AttributionLabel.DESIGN_LIMITATION,
            paired_rationale="Both aligned.",
        )
        assert pr.paired_attribution_label == AttributionLabel.DESIGN_LIMITATION

    def test_mismatched_scenario_id_rejected(self):
        u = self._make_eval("EE_S01", "umass_cs250")
        j = self._make_eval("EE_S02", "japan_discrete_math")  # wrong id
        with pytest.raises(ValidationError):
            PairedAttributionResult(
                scenario_id="EE_S01",
                umass_result=u,
                japan_result=j,
                paired_attribution_label=AttributionLabel.DESIGN_LIMITATION,
                paired_rationale="Mismatch.",
            )
