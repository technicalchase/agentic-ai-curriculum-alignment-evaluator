"""
schemas.py — Pydantic data models for the Agentic AI Curriculum Alignment Evaluator.

All models are validated on construction. Invalid inputs are rejected rather
than silently coerced, keeping every accepted result grounded in real data.

Data dictionary source:
  IBM SkillsBuild Sprint One POC Technical Charter (Randall, 2026), Section 2.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class BloomLevel(str, Enum):
    """Revised Bloom's Taxonomy levels (Anderson & Krathwohl, 2001)."""
    REMEMBER   = "Remember"
    UNDERSTAND = "Understand"
    APPLY      = "Apply"
    ANALYZE    = "Analyze"
    EVALUATE   = "Evaluate"
    CREATE     = "Create"


class AlignmentStatus(str, Enum):
    """Single-profile alignment verdict for one EvaluationResult."""
    ALIGNED                = "Aligned"
    MISALIGNED             = "Misaligned"
    INSUFFICIENT_INFORMATION = "Insufficient_Information"


class AttributionLabel(str, Enum):
    """Paired diagnostic attribution label (non-causal)."""
    DESIGN_LIMITATION      = "Consistent_With_Design_Limitation"
    CONTEXTUAL_ASSUMPTION  = "Consistent_With_Contextual_Assumption"
    INSUFFICIENT_INFORMATION = "Insufficient_Information"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class RuleItem(BaseModel):
    """A single curriculum rule with a verifiable identifier."""
    rule_id: str = Field(..., description="Unique identifier used for citation verification.")
    text: str    = Field(..., description="Human-readable rule text.")


class DiagnosticClaim(BaseModel):
    """
    A grounded claim supporting an alignment assessment.

    Every cited_id must be verified by the critic before the claim is accepted.
    If verification fails after two retries the containing EvaluationResult is
    downgraded to Insufficient_Information.
    """
    claim_text: str            = Field(..., description="Specific observation about alignment or mismatch.")
    cited_ids:  List[str]      = Field(..., min_length=1, description="Exact rule_id or scenario_id values.")


# ---------------------------------------------------------------------------
# Primary models
# ---------------------------------------------------------------------------

class InstitutionalProfile(BaseModel):
    """
    A synthetic curriculum profile for one institution.

    structural_rules and socio_communicative_norms are intentionally kept
    separate so that the evaluator can distinguish curricular failures from
    communication-preference mismatches.
    """
    profile_id:                 str              = Field(..., description="Unique fixture identifier (umass_cs250 or japan_discrete_math).")
    institution_name:           str              = Field(..., description="Human-readable institution name.")
    structural_rules:           List[RuleItem]   = Field(..., description="Verifiable curricular rules, prerequisites, and formal proof standards.")
    socio_communicative_norms:  List[RuleItem]   = Field(..., description="Hypothetical cultural/communicative expectations (isolated from structural rules).")
    bloom_baseline_level:       BloomLevel       = Field(..., description="Testable pedagogical target from Revised Bloom's Taxonomy.")

    def all_rule_ids(self) -> set[str]:
        """Return every rule_id defined in this profile."""
        ids: set[str] = set()
        for r in self.structural_rules:
            ids.add(r.rule_id)
        for r in self.socio_communicative_norms:
            ids.add(r.rule_id)
        return ids


class FeedbackScenario(BaseModel):
    """
    One synthetic evaluation fixture.

    The EE problem, student_attempt, and ai_feedback_text are held constant
    across both institutional profiles in a paired comparison.
    """
    scenario_id:              str  = Field(..., description="Unique test case ID anchored to the COMPSCI 250 EE problem.")
    student_attempt:          str  = Field(..., description="Synthetic student regular expression or proof snippet.")
    ai_feedback_text:         str  = Field(..., description="Synthetic AI feedback held constant across both profiles.")
    # Pre-defined expected labels (set before evaluation, not inferred from results)
    expected_umass_alignment:  AlignmentStatus  = Field(..., description="Pre-defined expected alignment for UMass profile.")
    expected_japan_alignment:  AlignmentStatus  = Field(..., description="Pre-defined expected alignment for Japan profile.")
    expected_attribution:      AttributionLabel = Field(..., description="Pre-defined expected paired attribution label.")
    is_negative_control:       bool             = Field(False, description="True when profiles should not differ in alignment outcome.")


class EvaluationResult(BaseModel):
    """
    Single-profile alignment result for one (scenario, profile) pair.

    Part of the N=20 single-profile accuracy calculation.
    """
    scenario_id:       str               = Field(..., description="Paired feedback scenario identifier.")
    profile_id:        str               = Field(..., description="Institutional profile evaluated in this run.")
    alignment_status:  AlignmentStatus   = Field(..., description="Single-profile alignment assessment.")
    claims:            List[DiagnosticClaim] = Field(default_factory=list, description="Grounded claims supporting the assessment.")
    retry_count:       int               = Field(0, ge=0, le=2, description="Number of citation retries performed (0–2).")


class PairedAttributionResult(BaseModel):
    """
    Cross-profile comparison result for one scenario.

    Part of the N=10 paired attribution accuracy calculation.
    """
    scenario_id:              str               = Field(..., description="Paired feedback scenario identifier (N=10).")
    umass_result:             EvaluationResult  = Field(..., description="Institutional evaluation under Profile A (umass_cs250).")
    japan_result:             EvaluationResult  = Field(..., description="Institutional evaluation under Profile B (japan_discrete_math).")
    paired_attribution_label: AttributionLabel  = Field(..., description="Non-causal paired attribution label.")
    paired_rationale:         str               = Field(..., description="Cross-profile synthesis explaining the attribution hypothesis.")

    @model_validator(mode="after")
    def scenario_ids_match(self) -> "PairedAttributionResult":
        if self.umass_result.scenario_id != self.scenario_id:
            raise ValueError("umass_result.scenario_id must match scenario_id")
        if self.japan_result.scenario_id != self.scenario_id:
            raise ValueError("japan_result.scenario_id must match scenario_id")
        return self


class BenchmarkReport(BaseModel):
    """
    Top-level output saved to results/benchmark_report.json.
    """
    paired_results:                  List[PairedAttributionResult]
    single_profile_correct:          int
    single_profile_total:            int
    single_profile_accuracy:         float
    paired_attribution_correct:      int
    paired_attribution_total:        int
    paired_attribution_accuracy:     float
    negative_control_summary:        str
    single_profile_target_met:       bool
    paired_attribution_target_met:   bool
    cross_profile_difference_found:  bool
    all_citations_valid:             bool
