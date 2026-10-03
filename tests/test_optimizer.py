from benefitflow_beta.models import BenefitRule, CategoryPreference, PlanRequest
from benefitflow_beta.optimizer import build_plan


def test_optimizer_respects_user_budget():
    req = PlanRequest(
        annual_out_of_pocket_budget=100,
        benefits=[BenefitRule(category="physiotherapy", coverage_percent=80, maximum_amount=750, period_kind="calendar_year", confidence="high")],
        preferences=[CategoryPreference(category="physiotherapy", priority=5, desired_visits=10, estimated_cost_per_visit=100)],
    )
    result = build_plan(req)
    assert result.estimated_user_paid <= 100
    assert result.services[0].visits == 5


def test_optimizer_applies_reasonable_customary_cap():
    req = PlanRequest(
        annual_out_of_pocket_budget=1000,
        benefits=[BenefitRule(category="massage therapy", coverage_percent=80, maximum_amount=1000, period_kind="benefit_year", reasonable_customary_cap=100, confidence="high")],
        preferences=[CategoryPreference(category="massage therapy", priority=5, desired_visits=1, estimated_cost_per_visit=140)],
    )
    result = build_plan(req)
    assert result.services[0].estimated_eligible_cost == 100
    assert result.services[0].estimated_insurer_paid == 80
    assert result.services[0].estimated_user_paid == 60


def test_optimizer_blocks_incomplete_semantics_for_manual_review():
    req = PlanRequest(
        annual_out_of_pocket_budget=500,
        benefits=[BenefitRule(category="vision", coverage_percent=100, maximum_amount=None, period_kind="unknown", confidence="low")],
        preferences=[CategoryPreference(category="vision", priority=4, desired_visits=1, estimated_cost_per_visit=300)],
    )
    result = build_plan(req)
    assert not result.services
    assert "vision" in result.manual_review_categories


def test_optimizer_blocks_explicit_semantic_manual_review_flag():
    req = PlanRequest(
        annual_out_of_pocket_budget=500,
        benefits=[
            BenefitRule(
                category="massage therapy",
                coverage_percent=80,
                maximum_amount=500,
                period_kind="annual_unspecified",
                confidence="medium",
                manual_review_required=True,
            )
        ],
        preferences=[CategoryPreference(category="massage therapy", priority=5, desired_visits=2, estimated_cost_per_visit=120)],
    )
    result = build_plan(req)
    assert not result.services
    assert "massage therapy" in result.manual_review_categories
    assert any("semantic ambiguity" in warning for warning in result.warnings)
