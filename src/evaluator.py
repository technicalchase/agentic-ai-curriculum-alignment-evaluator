"""
evaluator.py — Deterministic alignment evaluator for the Curriculum Alignment Evaluator POC.

This module implements the four-step pipeline described in the Sprint One
Technical Charter (Randall, 2026), Section 2:

  Step 1 — Input validation (Pydantic, handled in schemas.py and load helpers)
  Step 2 — Alignment review: compare feedback against each institutional profile
  Step 3 — Citation check: verify cited_ids via CitationCritic (up to 2 retries)
  Step 4 — Paired comparison and report

No LLM calls are made.  All alignment decisions are deterministic rule-based
comparisons so the POC is fully reproducible without an API key.

The evaluation logic works by checking structural rules and communicative norms
against keyword signals embedded in the ai_feedback_text, using lightweight
pattern matching that is explicitly documented and auditable.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from critic import CitationCritic
from schemas import (
    AlignmentStatus,
    AttributionLabel,
    DiagnosticClaim,
    EvaluationResult,
    FeedbackScenario,
    InstitutionalProfile,
    PairedAttributionResult,
)

# ---------------------------------------------------------------------------
# Rule-matching helpers
# ---------------------------------------------------------------------------

def _contains_any(text: str, patterns: List[str]) -> bool:
    """Return True if any pattern (case-insensitive substring) is found in text."""
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def _proof_language_present(feedback: str) -> bool:
    """True when the feedback uses formal proof vocabulary."""
    proof_markers = [
        "inductive", "induction", "proof", "prove", "formal", "formally",
        "by definition", "base case", "inductive step", "soundness", "completeness",
        "iff", "if and only if", "formal argument",
    ]
    return _contains_any(feedback, proof_markers)


def _dfa_reference_present(feedback: str) -> bool:
    """True when the feedback references finite automata concepts."""
    dfa_markers = [
        "dfa", "nfa", "finite automaton", "finite automata", "state machine",
        "transition", "accepting state", "parity state", "state-elimination",
        "state elimination", "equivalence theorem",
    ]
    return _contains_any(feedback, dfa_markers)


def _self_contradictory(feedback: str) -> bool:
    """
    Detect obvious self-contradictions: e.g. 'is incorrect … answer is correct'
    or 'is wrong … this is right'.

    Uses word-boundary patterns to avoid false positives like
    'does not correctly' matching as both negative and positive.
    """
    # Negative markers that explicitly signal an error was found
    neg_patterns = [
        r"\bincorrect\b",         # "is incorrect"
        r"\bwrong\b",             # "is wrong"
        r"\bnot correct\b",       # "not correct" as a phrase
        r"\bthis is wrong\b",
    ]
    # Positive markers that explicitly claim correctness AFTER the error mention
    pos_patterns = [
        r"\bthe answer is correct\b",
        r"\byour answer is correct\b",
        r"\bthis is correct\b",
        r"\bthe answer is right\b",
    ]
    text = feedback.lower()
    neg_found = any(re.search(p, text) for p in neg_patterns)
    pos_found = any(re.search(p, text) for p in pos_patterns)
    return neg_found and pos_found


def _feedback_identifies_error(feedback: str) -> bool:
    """True when the feedback specifically identifies a structural error."""
    error_markers = [
        "incorrect", "wrong", "not correct", "error", "flaw", "problem",
        "does not", "doesn't", "missing", "fails to", "you need", "you must",
        "consider", "rethink", "fix", "try",
    ]
    return _contains_any(feedback, error_markers)


def _has_counterexample(feedback: str) -> bool:
    """True when the feedback provides a concrete test string."""
    return bool(re.search(r"'[a-z]+'|\"[a-z]+\"|string.*for example|for example.*string|verify.*against", feedback.lower()))


def _feedback_gives_structural_diagnosis(feedback: str) -> bool:
    """
    True when the feedback provides a specific structural explanation of WHY
    the expression is wrong — not just a counter-example or a hint to try something.

    This distinguishes COMPSCI 250-level diagnostic feedback (SR07: identify
    the precise structural flaw) from vague hint-only or example-only feedback.

    The key signals are:
    - Explicit analysis of what the expression DOES that it shouldn't (or vice versa)
    - References to operator properties (union, precedence, parity tracking)
    - Analysis of which strings the expression accepts vs the target language
    - "which means" / "which shows" causal language linking the structure to the problem
    """
    structural_markers = [
        # Explicit structural analysis of the expression's behaviour
        "counts pairs", "allows any number", "constraint",
        "top-level union", "top level union", "operator precedence",
        "both branches", "simultaneously",
        "even-b", "even-a", "even parity",
        # Causal explanation linking expression structure to wrong language
        "which means it accepts", "which means it rejects",
        "which means it", "which shows",
        "accepts strings from", "accepts strings from either",
        # Structural terminology
        "subexpression", "outer group", "inner group",
        "precedence", "parsing",
        # Diagnosis with specific analytical technique
        "strings with zero",
        # Causal markers (only when explaining a structural relationship)
        "which means", "this means",
    ]
    return _contains_any(feedback, structural_markers)


def _feedback_just_confirms(feedback: str) -> bool:
    """True when feedback only confirms correctness without any explanatory content."""
    confirmatory = ["correct", "well done", "great work", "you successfully", "good job", "this completes"]
    explanatory  = [
        "because", "since", "this works", "this captures", "this is equivalent", "notice that",
        "which means", "which shows", "explanation", "justif", "induct", "proof",
        # Pattern-level explanations
        "directly matches", "tracks parity", "it tracks", "it captures", "parity",
        "concatenation", "union", "kleene", "language of strings", "even number",
        "connection", "reinforces", "formally", "which helps",
    ]
    has_confirm  = _contains_any(feedback, confirmatory)
    has_explain  = _contains_any(feedback, explanatory)
    return has_confirm and not has_explain


# ---------------------------------------------------------------------------
# Single-profile alignment engine
# ---------------------------------------------------------------------------

class AlignmentEngine:
    """
    Evaluates a FeedbackScenario against one InstitutionalProfile.

    The evaluation is deterministic and rule-based.  Each structural rule and
    communicative norm is checked against the feedback text; claims are
    generated with explicit cited_ids so the CitationCritic can verify them.
    """

    MAX_RETRIES = 2

    def __init__(self, profile: InstitutionalProfile) -> None:
        self.profile = profile

    def evaluate(self, scenario: FeedbackScenario) -> EvaluationResult:
        """
        Run Steps 2–3: alignment review + citation check with up to 2 retries.

        Returns an EvaluationResult with a verified alignment_status.
        """
        feedback = scenario.ai_feedback_text
        pid = self.profile.profile_id

        # Build initial claims
        claims, status = self._build_claims(scenario)

        # Step 3: citation check with up to MAX_RETRIES retries
        critic = CitationCritic(self.profile, scenario)
        retry_count = 0

        for attempt in range(self.MAX_RETRIES + 1):
            is_valid, bad_ids = critic.check_claims(claims)
            if is_valid:
                break
            # Retry: strip out claims with invalid citations
            claims = [c for c in claims if all(cid in critic.valid_ids for cid in c.cited_ids)]
            retry_count += 1

        is_valid, bad_ids = critic.check_claims(claims)
        if not is_valid or not claims:
            # Exhausted retries — downgrade to Insufficient_Information
            status = AlignmentStatus.INSUFFICIENT_INFORMATION
            claims = [
                DiagnosticClaim(
                    claim_text=(
                        f"Citation verification failed after {retry_count} retries. "
                        f"Unresolvable identifiers: {bad_ids}. Flagged for human review."
                    ),
                    cited_ids=[scenario.scenario_id],
                )
            ]

        return EvaluationResult(
            scenario_id=scenario.scenario_id,
            profile_id=pid,
            alignment_status=status,
            claims=claims,
            retry_count=retry_count,
        )

    # ------------------------------------------------------------------
    # Profile-specific alignment logic
    # ------------------------------------------------------------------

    def _build_claims(
        self, scenario: FeedbackScenario
    ) -> Tuple[List[DiagnosticClaim], AlignmentStatus]:
        """
        Produce diagnostic claims and an initial alignment status.

        Rules are applied in priority order; the first definitive finding
        (Misaligned or confirmed Aligned) terminates further checking.
        """
        feedback = scenario.ai_feedback_text
        sid = scenario.scenario_id
        pid = self.profile.profile_id

        claims: List[DiagnosticClaim] = []
        misaligned = False

        # --- Universal checks (apply to both profiles) ---

        # U1: Self-contradiction is a design failure regardless of curriculum
        if _self_contradictory(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback is self-contradictory: it identifies an error and then "
                    "claims the answer is correct within the same response. This is a "
                    "system-level failure independent of curriculum context."
                ),
                cited_ids=[sid],
            ))
            misaligned = True

        # --- Profile-specific checks ---
        if pid == "umass_cs250":
            claims_p, misaligned_p = self._check_umass(scenario, misaligned)
        else:
            claims_p, misaligned_p = self._check_japan(scenario, misaligned)

        claims.extend(claims_p)
        if misaligned_p:
            misaligned = True

        # Determine status
        if misaligned:
            status = AlignmentStatus.MISALIGNED
        else:
            status = AlignmentStatus.ALIGNED

        return claims, status

    def _check_umass(
        self, scenario: FeedbackScenario, already_misaligned: bool
    ) -> Tuple[List[DiagnosticClaim], bool]:
        """UMass COMPSCI 250 specific alignment rules."""
        feedback = scenario.ai_feedback_text
        sid = scenario.scenario_id
        claims: List[DiagnosticClaim] = []
        misaligned = already_misaligned

        # U-A: Feedback on a wrong answer must identify the structural flaw (SR07)
        correct_constructions = [
            "(aa|bb|(ab|ba)(aa|bb)*(ab|ba))*",
            "((aa)|(bb)|(ab|ba)((aa)|(bb))*(ab|ba))*",
            "((aa)|(bb)|(ab)(aa|bb)*(ba)|(ba)(aa|bb)*(ab))*",
        ]
        # Exact match only — substring matching causes false positives
        # (e.g. "(aa|bb)*" is a substring of "(aa|bb|(ab|ba)(aa|bb)*(ab|ba))*")
        student_is_correct = scenario.student_attempt.strip() in correct_constructions

        if not student_is_correct and not _feedback_identifies_error(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The student's answer appears incorrect but the feedback does not "
                    "identify any structural flaw. COMPSCI 250 requires feedback to "
                    "pinpoint the precise error (umass_SR07)."
                ),
                cited_ids=[sid, "umass_SR07"],
            ))
            misaligned = True

        # U-B: Proof-level justification must be required or confirmed (SR02, SR04)
        if student_is_correct and _feedback_just_confirms(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback confirms correctness without requiring or providing a "
                    "formal proof of correctness. COMPSCI 250 requires explicit "
                    "justification (umass_SR02, umass_SR04)."
                ),
                cited_ids=[sid, "umass_SR02", "umass_SR04"],
            ))
            misaligned = True

        # U-C: If a correct answer is confirmed with a proof or DFA explanation, that is aligned
        if student_is_correct and not _feedback_just_confirms(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback confirms the correct answer and provides supporting "
                    "explanation, satisfying the COMPSCI 250 proof and justification "
                    "requirements (umass_SR02, umass_CLO01)."
                ),
                cited_ids=[sid, "umass_SR02", "umass_CLO01"],
            ))

        # U-D: Error feedback at UMass requires proof or DFA reasoning to be fully aligned (SR02-SR05)
        if not student_is_correct and _feedback_identifies_error(feedback):
            if _proof_language_present(feedback) or _dfa_reference_present(feedback):
                claims.append(DiagnosticClaim(
                    claim_text=(
                        "The feedback correctly identifies the error and invokes formal "
                        "reasoning or DFA concepts consistent with COMPSCI 250 prerequisites "
                        "(umass_SR03, umass_SR05, umass_CLO02)."
                    ),
                    cited_ids=[sid, "umass_SR03", "umass_SR05", "umass_CLO02"],
                ))
            elif _feedback_gives_structural_diagnosis(feedback):
                # Structural diagnosis without formal proof — aligned at UMass
                # (SR07 requires pinpointing the precise flaw; structural analysis satisfies this)
                claims.append(DiagnosticClaim(
                    claim_text=(
                        "The feedback identifies the error and provides a structural "
                        "explanation of the flaw, satisfying the COMPSCI 250 requirement "
                        "to pinpoint the precise problem (umass_SR07, umass_CLO03)."
                    ),
                    cited_ids=[sid, "umass_SR07", "umass_CLO03"],
                ))
            else:
                # Error identified but only hinted — no structural diagnosis or proof
                # Misaligned at UMass: COMPSCI 250 requires pinpointing the flaw (umass_SR07)
                claims.append(DiagnosticClaim(
                    claim_text=(
                        "The feedback identifies that an error exists but provides only "
                        "a vague hint without structural analysis of the flaw. "
                        "COMPSCI 250 requires pinpointing the precise structural problem "
                        "(umass_SR07, umass_SR02)."
                    ),
                    cited_ids=[sid, "umass_SR07", "umass_SR02"],
                ))
                misaligned = True

        return claims, misaligned

    def _check_japan(
        self, scenario: FeedbackScenario, already_misaligned: bool
    ) -> Tuple[List[DiagnosticClaim], bool]:
        """Japan Discrete Mathematics specific alignment rules."""
        feedback = scenario.ai_feedback_text
        sid = scenario.scenario_id
        claims: List[DiagnosticClaim] = []
        misaligned = already_misaligned

        correct_constructions = [
            "(aa|bb|(ab|ba)(aa|bb)*(ab|ba))*",
            "((aa)|(bb)|(ab|ba)((aa)|(bb))*(ab|ba))*",
            "((aa)|(bb)|(ab)(aa|bb)*(ba)|(ba)(aa|bb)*(ab))*",
        ]
        student_is_correct = scenario.student_attempt.strip() in correct_constructions

        # J-0: Feedback incorrectly rejects a correct answer — design failure regardless of curriculum
        if student_is_correct and re.search(r"\bincorrect\b|\bwrong\b|\bnot correct\b", feedback.lower()):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback incorrectly marks the student's correct answer as wrong. "
                    "This is a factual error in the AI feedback and represents a design "
                    "limitation regardless of curriculum context (japan_CLO01, japan_SR01)."
                ),
                cited_ids=[sid, "japan_CLO01", "japan_SR01"],
            ))
            misaligned = True

        # J-A: DFA references are out-of-scope at this course level (SR03, SR04)
        if _dfa_reference_present(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback references DFA or finite automata concepts that are "
                    "explicitly out-of-scope for this course stage "
                    "(japan_SR03, japan_SR04). This may confuse students who have not "
                    "yet encountered automata theory."
                ),
                cited_ids=[sid, "japan_SR03", "japan_SR04"],
            ))
            misaligned = True

        # J-B: Demanding a formal proof exceeds course-level expectations regardless of correctness (SR02, SR03)
        if _proof_language_present(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback demands a formal inductive proof, which exceeds the "
                    "course-level prerequisite expectations for this exercise "
                    "(japan_SR02, japan_SR03)."
                ),
                cited_ids=[sid, "japan_SR02", "japan_SR03"],
            ))
            misaligned = True

        # J-C: Feedback on an incorrect answer that uses plain language and a counter-example is well-aligned
        if not student_is_correct and _feedback_identifies_error(feedback) and not misaligned:
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback identifies the error using accessible language consistent "
                    "with the course-level expectations (japan_SR05, japan_CLO02)."
                ),
                cited_ids=[sid, "japan_SR05", "japan_CLO02"],
            ))

        # J-D: Correct answer confirmed with brief feedback — this is acceptable at this level
        if student_is_correct and not misaligned and not _dfa_reference_present(feedback) and not _proof_language_present(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback correctly confirms the student's answer. Brief "
                    "confirmatory feedback is appropriate at this course level "
                    "(japan_CLO01, japan_CLO02)."
                ),
                cited_ids=[sid, "japan_CLO01", "japan_CLO02"],
            ))

        # J-E: Correct answer with explanation (DFA free) — still aligned and richer
        if student_is_correct and not misaligned and not _dfa_reference_present(feedback) and not _feedback_just_confirms(feedback):
            claims.append(DiagnosticClaim(
                claim_text=(
                    "The feedback confirms correctness and provides an explanation that "
                    "stays within scope, supporting course learning outcomes "
                    "(japan_CLO01, japan_SR06)."
                ),
                cited_ids=[sid, "japan_CLO01", "japan_SR06"],
            ))

        return claims, misaligned


# ---------------------------------------------------------------------------
# Paired comparison engine
# ---------------------------------------------------------------------------

class PairedComparisonEngine:
    """
    Step 4: Compare two EvaluationResults for the same scenario and assign
    a paired attribution label.
    """

    def compare(
        self,
        scenario: FeedbackScenario,
        umass_result: EvaluationResult,
        japan_result: EvaluationResult,
    ) -> PairedAttributionResult:
        """Produce a PairedAttributionResult for one scenario."""

        u_status = umass_result.alignment_status
        j_status = japan_result.alignment_status

        label, rationale = self._assign_label(scenario, u_status, j_status)

        return PairedAttributionResult(
            scenario_id=scenario.scenario_id,
            umass_result=umass_result,
            japan_result=japan_result,
            paired_attribution_label=label,
            paired_rationale=rationale,
        )

    @staticmethod
    def _assign_label(
        scenario: FeedbackScenario,
        u_status: AlignmentStatus,
        j_status: AlignmentStatus,
    ) -> Tuple[AttributionLabel, str]:
        """
        Attribution decision rules (deterministic):

        Both Misaligned
          → Consistent_With_Design_Limitation
            (the feedback fails regardless of curriculum — system-level issue)

        Both Aligned
          → Consistent_With_Design_Limitation
            (the feedback succeeds regardless of curriculum — no context gap)

        One Aligned, One Misaligned
          → Consistent_With_Contextual_Assumption
            (the feedback works in one context but not the other — context gap)

        Either Insufficient_Information
          → Insufficient_Information (flagged for human review)
        """
        ii = AlignmentStatus.INSUFFICIENT_INFORMATION

        if u_status == ii or j_status == ii:
            return (
                AttributionLabel.INSUFFICIENT_INFORMATION,
                (
                    f"One or both institutional evaluations returned Insufficient_Information "
                    f"(UMass: {u_status.value}, Japan: {j_status.value}). "
                    "The paired comparison cannot be completed without valid evidence from both "
                    "profiles. Flagged for human review."
                ),
            )

        if u_status == j_status:
            # Both agree — design-level finding
            if u_status == AlignmentStatus.MISALIGNED:
                return (
                    AttributionLabel.DESIGN_LIMITATION,
                    (
                        "The feedback is misaligned under both institutional profiles. "
                        "Because the misalignment is consistent regardless of curriculum "
                        "context, this pattern is consistent with a system design limitation "
                        "rather than a curriculum-specific contextual assumption. "
                        "The feedback problem does not depend on which institution's rules "
                        "are applied."
                    ),
                )
            else:
                # Both Aligned — no failure, but attribution still records this as design-level
                return (
                    AttributionLabel.DESIGN_LIMITATION,
                    (
                        "The feedback is aligned under both institutional profiles. "
                        "Because the feedback succeeds regardless of curriculum context, "
                        "its quality is consistent with a curriculum-independent (design-level) "
                        "property rather than a contextual assumption. "
                        "No curriculum-specific gap was identified."
                    ),
                )

        # Profiles disagree — contextual assumption
        aligned_profile   = "UMass COMPSCI 250" if u_status == AlignmentStatus.ALIGNED else "Japan Discrete Math"
        misaligned_profile = "Japan Discrete Math" if u_status == AlignmentStatus.ALIGNED else "UMass COMPSCI 250"

        return (
            AttributionLabel.CONTEXTUAL_ASSUMPTION,
            (
                f"The feedback is aligned under the {aligned_profile} profile but "
                f"misaligned under the {misaligned_profile} profile. "
                "Because the same feedback produces different alignment outcomes depending "
                "on which institutional profile is applied, this pattern is consistent "
                "with a contextual assumption embedded in the feedback — an assumption "
                "that holds in one curriculum context but not the other. "
                "This is a possible explanation, not a confirmed cause."
            ),
        )
