from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "recursive_enhancement_cycle.py"
spec = importlib.util.spec_from_file_location("recursive_enhancement_cycle", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_candidate_fingerprint_is_stable_and_source_specific():
    a = module.candidate_fingerprint("org/repo-a", "protocol.md", "abc123", "cursor")
    b = module.candidate_fingerprint("org/repo-a", "protocol.md", "abc123", "cursor")
    c = module.candidate_fingerprint("org/repo-b", "protocol.md", "abc123", "cursor")
    assert a == b
    assert a != c


def test_validate_candidate_rejects_foreign_mutation():
    candidate = {
        "candidate_id": "x",
        "source_repository": "org/foreign",
        "source_path": "protocol.md",
        "source_ref": "abc123",
        "concept_id": "test",
        "compatibility": "SAFE_REUSABLE",
        "observed_pattern": "pattern",
        "expected_benefitflow_value": "value",
        "affected_benefitflow_surfaces": ["control"],
        "foreign_mutation_requested": True,
    }
    errors = module.validate_candidate(candidate)
    assert any("foreign_mutation_requested" in error for error in errors)


def test_validate_candidate_rejects_wrong_target_repository():
    candidate = {
        "candidate_id": "x",
        "source_repository": "org/foreign",
        "source_path": "protocol.md",
        "source_ref": "abc123",
        "concept_id": "test",
        "compatibility": "ADAPT_REQUIRED",
        "observed_pattern": "pattern",
        "expected_benefitflow_value": "value",
        "affected_benefitflow_surfaces": ["control"],
        "foreign_mutation_requested": False,
        "target_repository": "org/foreign",
    }
    errors = module.validate_candidate(candidate)
    assert any("target_repository" in error for error in errors)


def test_validate_candidate_accepts_read_only_foreign_source():
    candidate = {
        "candidate_id": "x",
        "source_repository": "org/foreign",
        "source_path": "protocol.md",
        "source_ref": "abc123",
        "concept_id": "test",
        "compatibility": "SAFE_REUSABLE",
        "observed_pattern": "pattern",
        "expected_benefitflow_value": "value",
        "affected_benefitflow_surfaces": ["control"],
        "foreign_mutation_requested": False,
        "target_repository": "boberino93-bit/benefitflow",
    }
    candidate["fingerprint"] = module.candidate_fingerprint(
        candidate["source_repository"],
        candidate["source_path"],
        candidate["source_ref"],
        candidate["concept_id"],
    )
    assert module.validate_candidate(candidate) == []
