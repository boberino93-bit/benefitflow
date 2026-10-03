from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]
PeriodKind = Literal["calendar_year", "benefit_year", "rolling_months", "lifetime", "unknown"]


class BenefitRule(BaseModel):
    category: str
    coverage_percent: float | None = Field(default=None, ge=0, le=100)
    maximum_amount: float | None = Field(default=None, ge=0)
    period_kind: PeriodKind = "unknown"
    period_months: int | None = Field(default=None, ge=1)
    visit_limit: int | None = Field(default=None, ge=0)
    shared_pool_id: str | None = None
    shared_pool_maximum: float | None = Field(default=None, ge=0)
    reasonable_customary_cap: float | None = Field(default=None, ge=0)
    deductible_remaining: float = Field(default=0, ge=0)
    benefit_used_to_date: float = Field(default=0, ge=0)
    requires_referral: bool | None = None
    requires_prescription: bool | None = None
    confidence: Confidence = "low"
    evidence_excerpt: str = ""
    notes: list[str] = Field(default_factory=list)


class ParseResult(BaseModel):
    benefits: list[BenefitRule]
    warnings: list[str] = Field(default_factory=list)


class CategoryPreference(BaseModel):
    category: str
    priority: int = Field(default=3, ge=1, le=5)
    desired_visits: int = Field(default=1, ge=0, le=52)
    estimated_cost_per_visit: float | None = Field(default=None, gt=0)


class PlanRequest(BaseModel):
    annual_out_of_pocket_budget: float = Field(ge=0)
    benefits: list[BenefitRule]
    preferences: list[CategoryPreference]


class PlannedService(BaseModel):
    category: str
    visits: int
    estimated_cost_per_visit: float
    total_provider_cost: float
    estimated_eligible_cost: float
    estimated_insurer_paid: float
    estimated_user_paid: float
    priority: int
    confidence: Confidence
    rationale: str


class PlanResult(BaseModel):
    services: list[PlannedService]
    total_provider_cost: float
    estimated_eligible_cost: float
    estimated_insurer_paid: float
    estimated_user_paid: float
    unused_out_of_pocket_budget: float
    manual_review_categories: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Provider(BaseModel):
    provider_id: str
    name: str
    category: str
    city: str
    phone: str
    booking_channel: Literal["phone", "web", "manual"]
    synthetic: bool = True


class ProviderVerification(BaseModel):
    provider_id: str
    insurer_name: str
    accepting_new_patients: bool | None = None
    current_price: float | None = Field(default=None, gt=0)
    direct_billing: Literal["confirmed", "not_available", "unknown"] = "unknown"
    required_profile_fields: list[str] = Field(default_factory=list)
    referral_required: bool | None = None
    prescription_required: bool | None = None
    cancellation_policy: str = ""
    verified_at: datetime | None = None
    evidence_note: str = ""
    synthetic: bool = True


class VerificationRequest(BaseModel):
    provider_id: str
    insurer_name: str = ""


class BookingProposalRequest(BaseModel):
    provider_id: str
    category: str
    preferred_window: str
    insurer_name: str = ""
    plan_number: str = ""
    member_id: str = ""


class BookingProposal(BaseModel):
    proposal_id: str
    provider: Provider
    verification: ProviderVerification
    category: str
    preferred_window: str
    expected_cost: float
    insurer_name: str
    plan_number_masked: str
    member_id_masked: str
    approval_required: bool = True
    status: Literal["AWAITING_USER_APPROVAL"] = "AWAITING_USER_APPROVAL"


class BookingApprovalRequest(BaseModel):
    proposal_id: str
    approved: bool


class BookingResult(BaseModel):
    proposal_id: str
    status: Literal["READY_FOR_TRANSACTION_ADAPTER", "DECLINED"]
    next_action: str
    transaction_script: str = ""
