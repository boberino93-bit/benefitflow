from benefitflow_beta.parser import parse_benefits_text


def test_parser_extracts_annual_and_rolling_periods():
    text = (
        "Physiotherapy: 80% reimbursement, annual maximum $750 per calendar year.\n"
        "Vision care: 100% reimbursement up to $300 every 24 months."
    )
    result = parse_benefits_text(text)
    by_cat = {x.category: x for x in result.benefits}
    assert by_cat["physiotherapy"].coverage_percent == 80
    assert by_cat["physiotherapy"].maximum_amount == 750
    assert by_cat["physiotherapy"].period_kind == "calendar_year"
    assert by_cat["vision"].maximum_amount == 300
    assert by_cat["vision"].period_kind == "rolling_months"
    assert by_cat["vision"].period_months == 24


def test_parser_does_not_bleed_adjacent_category_values():
    text = (
        "Psychology: 70% reimbursement, annual maximum $1,000 per calendar year.\n"
        "Massage therapy: 80% reimbursement, annual maximum $600 per calendar year."
    )
    result = parse_benefits_text(text)
    by_cat = {x.category: x for x in result.benefits}
    assert by_cat["psychology"].maximum_amount == 1000
    assert by_cat["massage therapy"].maximum_amount == 600


def test_parser_keeps_per_visit_cap_separate_from_dynamic_rc():
    text = (
        "Physiotherapy: 80% reimbursement, subject to reasonable and customary limits, "
        "maximum $25 per visit, annual maximum $250 per calendar year."
    )
    result = parse_benefits_text(text)
    rule = {x.category: x for x in result.benefits}["physiotherapy"]

    assert rule.maximum_amount == 250
    assert rule.reasonable_customary_cap is None
    assert rule.manual_review_required is True
    assert any(limit.scope == "per_visit" and limit.amount == 25 for limit in rule.limits)
    assert any(limit.scope == "per_category" and limit.amount == 250 for limit in rule.limits)
    assert len(rule.eligible_charge_rules) == 1
    assert rule.eligible_charge_rules[0].method == "reasonable_customary"
    assert rule.eligible_charge_rules[0].external_lookup_required is True


def test_parser_preserves_annual_unknown_anchor_and_field_provenance():
    text = "Massage therapy: 80% reimbursement, $500 annually."
    result = parse_benefits_text(text)
    rule = {x.category: x for x in result.benefits}["massage therapy"]

    assert rule.maximum_amount == 500
    assert rule.period_kind == "annual_unspecified"
    assert rule.manual_review_required is True
    fields = {item.field for item in rule.field_evidence}
    assert "coverage_percent" in fields
    assert "period_kind" in fields
    assert "maximum_amount" in fields


def test_parser_does_not_select_largest_value_when_multiple_unbound_amounts_remain():
    text = (
        "Chiropractic: 80% reimbursement, $300 annually for one benefit component "
        "and $600 annually for another component."
    )
    result = parse_benefits_text(text)
    rule = {x.category: x for x in result.benefits}["chiropractic"]

    assert rule.maximum_amount is None
    assert rule.manual_review_required is True
    assert any("numeric magnitude was not used" in note for note in rule.notes)
