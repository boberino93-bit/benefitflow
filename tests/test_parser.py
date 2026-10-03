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
