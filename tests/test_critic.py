"""
test_critic.py — Unit tests for the CitationCritic.

Verifies that:
  - Valid citations pass.
  - Invalid citations are rejected and reported.
  - The valid_ids pool contains both rule_ids and scenario_id.
"""
from __future__ import annotations

from schemas import DiagnosticClaim
from critic import CitationCritic


class TestCitationCritic:
    def test_valid_rule_citation_passes(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claim = DiagnosticClaim(claim_text="Test.", cited_ids=["umass_SR01"])
        is_valid, bad = critic.check_claim(claim)
        assert is_valid
        assert bad == []

    def test_scenario_id_is_valid(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claim = DiagnosticClaim(claim_text="Test.", cited_ids=[sc.scenario_id])
        is_valid, bad = critic.check_claim(claim)
        assert is_valid

    def test_invalid_id_rejected(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claim = DiagnosticClaim(claim_text="Test.", cited_ids=["NONEXISTENT_ID"])
        is_valid, bad = critic.check_claim(claim)
        assert not is_valid
        assert "NONEXISTENT_ID" in bad

    def test_mixed_valid_invalid(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claim = DiagnosticClaim(claim_text="Test.", cited_ids=["umass_SR01", "BAD_ID"])
        is_valid, bad = critic.check_claim(claim)
        assert not is_valid
        assert "BAD_ID" in bad
        assert "umass_SR01" not in bad

    def test_check_claims_all_valid(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claims = [
            DiagnosticClaim(claim_text="A.", cited_ids=["umass_SR01"]),
            DiagnosticClaim(claim_text="B.", cited_ids=["umass_CLO01"]),
        ]
        is_valid, bad = critic.check_claims(claims)
        assert is_valid
        assert bad == []

    def test_check_claims_some_invalid(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        claims = [
            DiagnosticClaim(claim_text="A.", cited_ids=["umass_SR01"]),
            DiagnosticClaim(claim_text="B.", cited_ids=["BAD_1", "BAD_2"]),
        ]
        is_valid, bad = critic.check_claims(claims)
        assert not is_valid
        assert "BAD_1" in bad
        assert "BAD_2" in bad

    def test_valid_ids_includes_scenario(self, umass_profile, all_scenarios):
        sc = all_scenarios[0]
        critic = CitationCritic(umass_profile, sc)
        assert sc.scenario_id in critic.valid_ids

    def test_japan_profile_ids_separate_from_umass(self, umass_profile, japan_profile, all_scenarios):
        sc = all_scenarios[0]
        umass_critic = CitationCritic(umass_profile, sc)
        japan_critic = CitationCritic(japan_profile, sc)
        # UMass rule is not valid under Japan pool
        assert "umass_SR01" not in japan_critic.valid_ids
        # Japan rule is not valid under UMass pool
        assert "japan_SR01" not in umass_critic.valid_ids
