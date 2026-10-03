from __future__ import annotations

from collections import defaultdict

from .models import PlanRequest, PlanResult, PlannedService

DEFAULT_COSTS = {
    "physiotherapy": 110.0,
    "massage therapy": 125.0,
    "chiropractic": 75.0,
    "psychology": 220.0,
    "acupuncture": 105.0,
    "naturopathy": 150.0,
    "podiatry": 120.0,
    "vision": 250.0,
    "dental": 180.0,
}


def build_plan(req: PlanRequest) -> PlanResult:
    benefit_map = {b.category.lower(): b for b in req.benefits}
    candidates: list[dict] = []
    warnings: list[str] = []
    manual_review: list[str] = []

    for pref in req.preferences:
        key = pref.category.lower()
        benefit = benefit_map.get(key)
        if not benefit:
            warnings.append(f"No parsed benefit line found for {pref.category}; it was not scheduled.")
            continue
        if benefit.coverage_percent is None or benefit.maximum_amount is None or benefit.period_kind == "unknown":
            warnings.append(f"{pref.category} has incomplete benefit semantics and requires manual review before planning.")
            manual_review.append(pref.category)
            continue
        if benefit.shared_pool_id or benefit.shared_pool_maximum is not None:
            warnings.append(f"{pref.category} participates in a shared pool; beta does not auto-optimize this without reviewed pool data.")
            manual_review.append(pref.category)
            continue

        cost = float(pref.estimated_cost_per_visit or DEFAULT_COSTS.get(key, 120.0))
        max_visits = pref.desired_visits
        if benefit.visit_limit is not None:
            max_visits = min(max_visits, benefit.visit_limit)

        for visit_index in range(max_visits):
            eligible = min(cost, benefit.reasonable_customary_cap) if benefit.reasonable_customary_cap else cost
            candidates.append({
                "category": pref.category,
                "priority": pref.priority,
                "cost": cost,
                "eligible": eligible,
                "coverage": benefit.coverage_percent / 100.0,
                "maximum": float(benefit.maximum_amount),
                "used_to_date": float(benefit.benefit_used_to_date),
                "deductible_remaining": float(benefit.deductible_remaining),
                "confidence": benefit.confidence,
                "visit_index": visit_index,
            })

    def score(c: dict) -> tuple[float, float]:
        reimbursable = c["eligible"] * c["coverage"]
        oop = max(0.01, c["cost"] - reimbursable)
        return (float(c["priority"]), reimbursable / oop)

    candidates.sort(key=score, reverse=True)
    remaining_budget = float(req.annual_out_of_pocket_budget)
    insurer_used: dict[str, float] = defaultdict(float)
    deductible_left: dict[str, float] = {}
    accepted: list[dict] = []

    for c in candidates:
        cat = c["category"]
        deductible_left.setdefault(cat, c["deductible_remaining"])
        eligible_after_deductible = c["eligible"]
        applied_deductible = min(deductible_left[cat], eligible_after_deductible)
        eligible_after_deductible -= applied_deductible
        potential_insurer = eligible_after_deductible * c["coverage"]
        remaining_max = max(0.0, c["maximum"] - c["used_to_date"] - insurer_used[cat])
        insurer_pay = min(potential_insurer, remaining_max)
        user_pay = max(0.0, c["cost"] - insurer_pay)
        if user_pay > remaining_budget + 1e-9:
            continue
        remaining_budget -= user_pay
        deductible_left[cat] -= applied_deductible
        insurer_used[cat] += insurer_pay
        accepted.append({**c, "insurer_pay": insurer_pay, "user_pay": user_pay, "applied_deductible": applied_deductible})

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in accepted:
        grouped[item["category"]].append(item)

    services: list[PlannedService] = []
    for category, items in grouped.items():
        provider_cost = sum(i["cost"] for i in items)
        eligible_cost = sum(i["eligible"] for i in items)
        insurer_paid = sum(i["insurer_pay"] for i in items)
        user_paid = sum(i["user_pay"] for i in items)
        services.append(PlannedService(
            category=category,
            visits=len(items),
            estimated_cost_per_visit=items[0]["cost"],
            total_provider_cost=round(provider_cost, 2),
            estimated_eligible_cost=round(eligible_cost, 2),
            estimated_insurer_paid=round(insurer_paid, 2),
            estimated_user_paid=round(user_paid, 2),
            priority=items[0]["priority"],
            confidence=items[0]["confidence"],
            rationale="Scheduled only within the user's requested visit count and out-of-pocket budget, using the parsed eligible-charge cap and remaining benefit maximum where available.",
        ))

    services.sort(key=lambda s: (-s.priority, s.category))
    return PlanResult(
        services=services,
        total_provider_cost=round(sum(s.total_provider_cost for s in services), 2),
        estimated_eligible_cost=round(sum(s.estimated_eligible_cost for s in services), 2),
        estimated_insurer_paid=round(sum(s.estimated_insurer_paid for s in services), 2),
        estimated_user_paid=round(sum(s.estimated_user_paid for s in services), 2),
        unused_out_of_pocket_budget=round(max(0.0, remaining_budget), 2),
        manual_review_categories=sorted(set(manual_review)),
        warnings=warnings,
    )
