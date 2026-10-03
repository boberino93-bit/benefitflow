"""
Proposed BenefitFlow R1 adversarial acceptance tests.

RESEARCH ARTIFACT ONLY.
These tests intentionally describe the target hardened behavior; they are not
accepted application code until Manager/Primary disposition.
"""

import pytest

from benefitflow_beta.parser import parse_benefits_text
from benefitflow_beta.models import BenefitRule, CategoryPreference, PlanRequest
from benefitflow_beta.optimizer import build_plan


@pytest.mark.xfail(reason="Current schema conflates per-visit cap with annual maximum")
def test_parser_does_not_promote_per_visit_cap_to_annual_maximum():
    result = parse_benefits_text(
        "Psychologists and social workers: 100% reimbursement, "
        "$75 per visit up to 10 visits per year."
    )
    rule = {x.category: x for x in result.benefits}["psychology"]
    assert rule.maximum_amount is None or rule.maximum_amount != 75


@pytest.mark.xfail(reason="Current R&C heuristic chooses the smallest dollar value")
def test_parser_does_not_label_contractual_per_visit_limit_as_rc():
    result = parse_benefits_text(
        "Massage therapy: 80% reimbursement, subject to reasonable and customary "
        "charges, maximum $25 per visit and $250 per year."
    )
    rule = {x.category: x for x in result.benefits}["massage therapy"]
    assert rule.reasonable_customary_cap is None


@pytest.mark.xfail(reason="Current parser does not construct structured shared pools")
def test_combined_pool_requires_structured_pool_or_manual_review():
    result = parse_benefits_text(
        "Physiotherapy: 100% reimbursement, $300 per year per practitioner "
        "and combined maximum $500 per calendar year."
    )
    rule = {x.category: x for x in result.benefits}["physiotherapy"]
    assert rule.shared_pool_id is not None or "physiotherapy" in getattr(result, "manual_review_categories", [])


@pytest.mark.xfail(reason="Current maximum_amount is always treated as insurer-payment ceiling")
def test_optimizer_distinguishes_max_eligible_expense_from_max_insurer_payment():
    req = PlanRequest(
        annual_out_of_pocket_budget=1000,
        benefits=[
            BenefitRule(
                category="chiropractic",
                coverage_percent=80,
                maximum_amount=500,  # target model must mark this as eligible-expense basis
                period_kind="calendar_year",
                reasonable_customary_cap=60,
                confidence="high",
            )
        ],
        preferences=[
            CategoryPreference(
                category="chiropractic",
                priority=5,
                desired_visits=10,
                estimated_cost_per_visit=75,
            )
        ],
    )
    result = build_plan(req)
    assert result.estimated_insurer_paid == 400
    assert result.estimated_user_paid == 350


@pytest.mark.xfail(reason="Bare annual currently maps to benefit_year")
def test_bare_annually_keeps_reset_anchor_unknown():
    result = parse_benefits_text("Vision care: 100% reimbursement, maximum $300 annually.")
    rule = {x.category: x for x in result.benefits}["vision"]
    assert rule.period_kind == "unknown"


@pytest.mark.xfail(reason="Waiting periods are not represented as eligibility gates")
def test_waiting_period_prevents_high_confidence_auto_planning():
    result = parse_benefits_text(
        "Vision care: 100% reimbursement, $300 maximum every 24 months. "
        "One-year waiting period applies."
    )
    rule = {x.category: x for x in result.benefits}["vision"]
    assert rule.confidence != "high"
