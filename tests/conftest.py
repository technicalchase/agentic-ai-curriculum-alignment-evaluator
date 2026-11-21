"""
conftest.py — pytest shared fixtures for the Curriculum Alignment Evaluator test suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make src/ importable from tests/
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from schemas import FeedbackScenario, InstitutionalProfile


@pytest.fixture(scope="session")
def umass_profile() -> InstitutionalProfile:
    path = REPO_ROOT / "data" / "umass_cs250.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return InstitutionalProfile.model_validate(data)


@pytest.fixture(scope="session")
def japan_profile() -> InstitutionalProfile:
    path = REPO_ROOT / "data" / "japan_discrete_math.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return InstitutionalProfile.model_validate(data)


@pytest.fixture(scope="session")
def all_scenarios() -> list[FeedbackScenario]:
    path = REPO_ROOT / "data" / "scenarios.json"
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    scenarios = []
    for item in raw:
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        scenarios.append(FeedbackScenario.model_validate(clean))
    return scenarios
