# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0
"""Deterministic dialectic memory validation helpers.

This module is intentionally pure: it does not read or write OpenViking memory,
does not mutate skills, and does not promote proposals. Callers can store
proposal records through the normal memory-template/session-commit pipeline and
use these helpers to decide whether a proposal is even eligible for a
low-risk, reversible promotion lane.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ReceiptStatus(str, Enum):
    """Receipt outcome used for promotion evidence."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class RiskClass(str, Enum):
    """Dialectic proposal risk class."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROTECTED = "protected"


class PromotionStatus(str, Enum):
    """Human-visible proposal lifecycle status."""

    DRAFT = "draft"
    NEEDS_APPROVAL = "needs_approval"
    ELIGIBLE_LOW_RISK = "eligible_low_risk"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ProtectedCategory(str, Enum):
    """Categories that always require explicit approval."""

    IDENTITY = "identity"
    PERMISSIONS = "permissions"
    CREDENTIALS = "credentials"
    POLICY = "policy"
    PRODUCTION_BEHAVIOR = "production_behavior"
    DESTRUCTIVE_ACTIONS = "destructive_actions"
    SKILL_CODE = "skill_code"


PROTECTED_CATEGORIES = frozenset(item.value for item in ProtectedCategory)


def _clean(value: str) -> str:
    return " ".join(value.split())


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class EvidenceReference(BaseModel):
    """A concrete, replayable receipt referenced by a proposal."""

    model_config = ConfigDict(extra="forbid")

    uri: str = Field(..., min_length=1)
    receipt_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    status: ReceiptStatus = ReceiptStatus.UNKNOWN
    independence_key: str | None = None

    @field_validator("uri", "receipt_id", "source", "independence_key", mode="before")
    @classmethod
    def _strip_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = _clean(value)
            return value or None
        return value

    def is_successful(self) -> bool:
        return self.status is ReceiptStatus.SUCCESS

    def independent_key(self) -> str:
        return self.independence_key or self.source or self.receipt_id


class EvalGate(BaseModel):
    """A named evaluation gate result."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    passed: bool
    receipt_id: str | None = None

    @field_validator("name", "receipt_id", mode="before")
    @classmethod
    def _strip_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = _clean(value)
            return value or None
        return value


class DialecticScope(BaseModel):
    """The proposal's intended blast radius."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=1)
    categories: tuple[str, ...] = Field(default_factory=tuple)
    reversible: bool = False

    @field_validator("summary", mode="before")
    @classmethod
    def _strip_summary(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _clean(value)
        return value

    @field_validator("categories", mode="before")
    @classmethod
    def _normalize_categories(cls, value: Any) -> Any:
        if value is None:
            return ()
        if isinstance(value, str):
            value = [part for part in value.replace(",", " ").split() if part]
        return tuple(str(item).strip().lower().replace("-", "_") for item in value if str(item).strip())

    def protected_categories(self) -> tuple[str, ...]:
        return tuple(category for category in self.categories if category in PROTECTED_CATEGORIES)


class DialecticProposal(BaseModel):
    """Schema for a dialectic/self-improvement memory proposal."""

    model_config = ConfigDict(extra="forbid")

    proposal_id: str | None = None
    claim: str = Field(..., min_length=1)
    counterclaim: str = Field(..., min_length=1)
    synthesis: str = Field(..., min_length=1)
    evidence_references: tuple[EvidenceReference, ...] = Field(default_factory=tuple)
    confidence: float = Field(..., ge=0.0, le=1.0)
    falsifier: str = Field(..., min_length=1)
    risk_class: RiskClass
    scope: DialecticScope
    expiry: str = Field(..., min_length=1)
    promotion_status: PromotionStatus = PromotionStatus.DRAFT
    unresolved_contradiction: bool = False
    eval_gates: tuple[EvalGate, ...] = Field(default_factory=tuple)

    @field_validator("proposal_id", "claim", "counterclaim", "synthesis", "falsifier", "expiry", mode="before")
    @classmethod
    def _strip_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = _clean(value)
            return value or None
        return value

    @field_validator("expiry")
    @classmethod
    def _validate_expiry_format(cls, value: str) -> str:
        _parse_datetime(value)
        return value

    def expires_at(self) -> datetime:
        return _parse_datetime(self.expiry)


class DialecticValidationResult(BaseModel):
    """Deterministic validation outcome."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class DialecticPromotionEligibility(BaseModel):
    """Low-risk promotion eligibility outcome."""

    model_config = ConfigDict(extra="forbid")

    eligible: bool
    requires_approval: bool
    reasons: tuple[str, ...] = ()
    protected_categories: tuple[str, ...] = ()
    successful_independent_receipts: int = 0


def parse_proposal(payload: DialecticProposal | dict[str, Any]) -> DialecticProposal:
    """Parse a proposal payload using the dialectic schema."""

    if isinstance(payload, DialecticProposal):
        return payload
    return DialecticProposal.model_validate(payload)


def validate_proposal(
    payload: DialecticProposal | dict[str, Any],
    *,
    now: datetime | None = None,
) -> DialecticValidationResult:
    """Validate proposal shape and deterministic promotion prerequisites."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        proposal = parse_proposal(payload)
    except ValidationError as exc:
        return DialecticValidationResult(
            valid=False,
            errors=tuple(f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in exc.errors()),
        )

    if len(proposal.evidence_references) == 0:
        errors.append("evidence_references must include at least one receipt")
    if len(proposal.eval_gates) == 0:
        warnings.append("eval_gates is empty; low-risk promotion will be ineligible")
    if proposal.scope.protected_categories():
        warnings.append("protected scope category requires approval")
    if proposal.risk_class is RiskClass.PROTECTED:
        warnings.append("protected risk class requires approval")
    if now is not None:
        current = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        if proposal.expires_at() <= current.astimezone(timezone.utc):
            errors.append("expiry must be in the future")

    return DialecticValidationResult(valid=not errors, errors=tuple(errors), warnings=tuple(warnings))


def low_risk_promotion_eligibility(
    payload: DialecticProposal | dict[str, Any],
    *,
    now: datetime | None = None,
) -> DialecticPromotionEligibility:
    """Return whether a proposal qualifies for the low-risk reversible lane."""

    validation = validate_proposal(payload, now=now)
    if not validation.valid:
        return DialecticPromotionEligibility(
            eligible=False,
            requires_approval=False,
            reasons=validation.errors,
        )

    proposal = parse_proposal(payload)
    reasons: list[str] = []
    protected_categories = proposal.scope.protected_categories()
    requires_approval = bool(protected_categories) or proposal.risk_class is RiskClass.PROTECTED

    successful_keys = {
        receipt.independent_key()
        for receipt in proposal.evidence_references
        if receipt.is_successful()
    }

    if proposal.risk_class is not RiskClass.LOW:
        reasons.append("risk_class must be low")
    if proposal.confidence < 0.90:
        reasons.append("confidence must be >= 0.90")
    if len(successful_keys) < 2:
        reasons.append("requires at least two independent successful receipts")
    if proposal.unresolved_contradiction:
        reasons.append("unresolved contradiction present")
    if not proposal.eval_gates or not all(gate.passed for gate in proposal.eval_gates):
        reasons.append("eval gates must all pass")
    if not proposal.scope.reversible:
        reasons.append("scope must be reversible")
    if requires_approval:
        reasons.append("protected categories or protected risk class require approval")
    if proposal.promotion_status in {PromotionStatus.REJECTED, PromotionStatus.EXPIRED}:
        reasons.append("promotion_status is terminal")

    return DialecticPromotionEligibility(
        eligible=not reasons,
        requires_approval=requires_approval,
        reasons=tuple(reasons),
        protected_categories=protected_categories,
        successful_independent_receipts=len(successful_keys),
    )
