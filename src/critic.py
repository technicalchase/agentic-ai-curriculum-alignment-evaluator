"""
critic.py — Deterministic citation verification for the Curriculum Alignment Evaluator.

The critic checks that every identifier cited in a DiagnosticClaim exists in
the relevant InstitutionalProfile or FeedbackScenario.  If any cited_id is
invalid the claim is rejected.  The evaluator may retry up to two times; if
the claim still contains invalid citations on the third attempt the containing
EvaluationResult is downgraded to Insufficient_Information.

No probabilistic logic lives here — the critic is a deterministic guardrail.
"""

from __future__ import annotations

from typing import List, Tuple

from schemas import DiagnosticClaim, FeedbackScenario, InstitutionalProfile


class CitationCritic:
    """
    Verifies that every cited_id in a DiagnosticClaim resolves to a known
    identifier in the given profile or scenario.

    Valid identifiers are drawn from:
      - InstitutionalProfile.structural_rules[*].rule_id
      - InstitutionalProfile.socio_communicative_norms[*].rule_id
      - FeedbackScenario.scenario_id
    """

    def __init__(self, profile: InstitutionalProfile, scenario: FeedbackScenario) -> None:
        self._valid_ids: set[str] = profile.all_rule_ids()
        self._valid_ids.add(scenario.scenario_id)
        self._profile_id = profile.profile_id
        self._scenario_id = scenario.scenario_id

    def check_claim(self, claim: DiagnosticClaim) -> Tuple[bool, List[str]]:
        """
        Validate all cited_ids in a single claim.

        Returns
        -------
        (is_valid, bad_ids)
            is_valid  — True if every cited_id resolves; False otherwise.
            bad_ids   — List of unresolvable identifiers (empty when valid).
        """
        bad_ids = [cid for cid in claim.cited_ids if cid not in self._valid_ids]
        return len(bad_ids) == 0, bad_ids

    def check_claims(self, claims: List[DiagnosticClaim]) -> Tuple[bool, List[str]]:
        """
        Validate all claims in a list.

        Returns
        -------
        (all_valid, bad_ids)
            all_valid — True when every claim passes.
            bad_ids   — Deduplicated list of all unresolvable identifiers.
        """
        all_bad: set[str] = set()
        for claim in claims:
            _, bad = self.check_claim(claim)
            all_bad.update(bad)
        return len(all_bad) == 0, sorted(all_bad)

    @property
    def valid_ids(self) -> set[str]:
        """Read-only view of the identifier pool used for verification."""
        return frozenset(self._valid_ids)
