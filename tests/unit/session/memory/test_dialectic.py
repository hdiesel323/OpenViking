# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0

import json
from datetime import datetime, timezone
from pathlib import Path

from openviking.prompts.manager import PromptManager
from openviking.session.memory.dialectic import (
    DialecticProposal,
    low_risk_promotion_eligibility,
    validate_proposal,
)
from openviking.session.memory.memory_type_registry import MemoryTypeRegistry

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "dialectic"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_dialectic_memory_template_loads_from_registry():
    memory_dir = PromptManager._get_bundled_templates_dir() / "memory"
    registry = MemoryTypeRegistry(load_schemas=False)
    registry.load_from_yaml(str(memory_dir / "dialectic_proposals.yaml"))

    schema = registry.get("dialectic_proposals")

    assert schema is not None
    assert schema.stage == "agent"
    assert schema.operation_mode == "add_only"
    assert schema.peer_enabled is True
    assert "claim" in {field.name for field in schema.fields}
    assert schema.embedding_template is not None
    assert "{{ synthesis }}" in schema.embedding_template


def test_low_risk_proposal_is_eligible_with_two_independent_successful_receipts():
    proposal = DialecticProposal.model_validate(_fixture("eligible_low_risk.json"))

    validation = validate_proposal(proposal, now=datetime(2026, 8, 1, tzinfo=timezone.utc))
    eligibility = low_risk_promotion_eligibility(
        proposal,
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert validation.valid is True
    assert eligibility.eligible is True
    assert eligibility.requires_approval is False
    assert eligibility.successful_independent_receipts == 2


def test_protected_categories_always_require_approval():
    proposal = DialecticProposal.model_validate(_fixture("protected_credentials.json"))

    eligibility = low_risk_promotion_eligibility(
        proposal,
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert eligibility.eligible is False
    assert eligibility.requires_approval is True
    assert eligibility.protected_categories == ("credentials", "permissions")
    assert "protected categories or protected risk class require approval" in eligibility.reasons


def test_unresolved_contradiction_blocks_low_risk_eligibility():
    payload = _fixture("eligible_low_risk.json")
    payload["unresolved_contradiction"] = True

    eligibility = low_risk_promotion_eligibility(
        payload,
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert eligibility.eligible is False
    assert "unresolved contradiction present" in eligibility.reasons


def test_failed_eval_gate_blocks_low_risk_eligibility():
    payload = _fixture("eligible_low_risk.json")
    payload["eval_gates"][0]["passed"] = False

    eligibility = low_risk_promotion_eligibility(
        payload,
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert eligibility.eligible is False
    assert "eval gates must all pass" in eligibility.reasons


def test_invalid_fixture_returns_deterministic_validation_errors():
    validation = validate_proposal(
        _fixture("invalid_missing_synthesis.json"),
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert validation.valid is False
    assert any("synthesis" in error for error in validation.errors)
