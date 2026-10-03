from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

from pypdf import PdfReader

from .models import (
    BenefitLimit,
    BenefitRule,
    EligibleChargeRule,
    FieldEvidence,
    ParseResult,
)


@dataclass(frozen=True)
class CategoryDef:
    name: str
    keywords: tuple[str, ...]


CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef("physiotherapy", ("physiotherapy", "physiotherapist", "physical therapy")),
    CategoryDef("massage therapy", ("massage therapy", "massage therapist", "rmt")),
    CategoryDef("chiropractic", ("chiropractic", "chiropractor")),
    CategoryDef("psychology", ("psychology", "psychologist", "psychotherapy", "counsellor", "counselor")),
    CategoryDef("acupuncture", ("acupuncture", "acupuncturist")),
    CategoryDef("naturopathy", ("naturopath", "naturopathy")),
    CategoryDef("podiatry", ("podiatry", "podiatrist", "chiropodist")),
    CategoryDef("vision", ("vision", "optometrist", "eyeglasses", "contact lenses")),
    CategoryDef("dental", ("dental", "dentist", "orthodont")),
)

_PERCENT = re.compile(r"\b(100|\d{1,2})\s*%")
_MONEY = re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)")
_VISITS = re.compile(r"\b(?:maximum|max(?:imum)? of|up to)\s*(\d{1,2})\s*(?:visits?|treatments?|sessions?)", re.I)
_MONTH_PERIOD = re.compile(r"(?:every|per|within)\s+(\d{1,2})\s+months?", re.I)
_PER_VISIT_MONEY = (
    re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:per|/)\s*(?:visit|treatment|session)\b", re.I),
    re.compile(r"(?:per\s+(?:visit|treatment|session)|(?:visit|treatment|session)\s+maximum)\s*(?:of|:|is)?\s*\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.I),
)
_ANNUAL_MONEY = (
    re.compile(r"(?:annual|yearly)\s+(?:benefit\s+)?(?:maximum|max|limit)\s*(?:of|:|is)?\s*\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.I),
    re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:per|/)\s*(?:calendar\s+|benefit\s+)?year\b", re.I),
)
_RC_TERM = re.compile(r"reasonable\s+(?:and|&)\s+customary|\br&c\b|eligible\s+charge", re.I)
_RC_FIXED = (
    re.compile(r"(?:reasonable\s+(?:and|&)\s+customary|\br&c\b|eligible\s+charge)\s*(?:limit|maximum|max|cap)?\s*(?:of|:|is)?\s*\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.I),
    re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:reasonable\s+(?:and|&)\s+customary|\br&c\b|eligible\s+charge)", re.I),
)


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _blocks(lines: list[str], keywords: Iterable[str]) -> list[str]:
    all_keywords = tuple(k for cat in CATEGORIES for k in cat.keywords)
    lowered = [line.lower() for line in lines]
    hits: list[str] = []
    for idx, line in enumerate(lowered):
        if not any(k in line for k in keywords):
            continue
        block = lines[idx]
        if idx + 1 < len(lines):
            nxt = lowered[idx + 1]
            if not any(k in nxt for k in all_keywords) and len(block) < 380:
                block += " " + lines[idx + 1]
        hits.append(block.strip())
    return hits


def _money_values(matches: Iterable[str]) -> list[float]:
    return [float(value.replace(",", "")) for value in matches]


def _unique(values: Iterable[float]) -> list[float]:
    return list(dict.fromkeys(values))


def _period(text: str) -> tuple[str, int | None]:
    lower = text.lower()
    if "lifetime" in lower:
        return "lifetime", None
    m = _MONTH_PERIOD.search(lower)
    if m:
        return "rolling_months", int(m.group(1))
    if "calendar year" in lower:
        return "calendar_year", 12
    if "benefit year" in lower or "plan year" in lower or "policy year" in lower:
        return "benefit_year", 12
    if re.search(r"\b(?:per year|annual|annually|yearly)\b", lower):
        return "annual_unspecified", 12
    return "unknown", None


def _per_visit_amounts(text: str) -> list[float]:
    values: list[float] = []
    for pattern in _PER_VISIT_MONEY:
        values.extend(_money_values(pattern.findall(text)))
    return _unique(values)


def _annual_amounts(text: str) -> list[float]:
    values: list[float] = []
    for pattern in _ANNUAL_MONEY:
        values.extend(_money_values(pattern.findall(text)))
    return _unique(values)


def _maximum(text: str, period_kind: str) -> tuple[float | None, bool]:
    """Return a legacy category maximum and whether its binding is ambiguous.

    The beta keeps `maximum_amount` for backward compatibility, but no longer
    chooses a semantic maximum merely because it is the largest dollar value.
    """
    if period_kind == "unknown":
        return None, False

    annual = _annual_amounts(text)
    if len(annual) == 1:
        return annual[0], False
    if len(annual) > 1:
        return None, True

    all_amounts = _unique(_money_values(_MONEY.findall(text)))
    per_visit = set(_per_visit_amounts(text))
    remaining = [amount for amount in all_amounts if amount not in per_visit]
    if len(remaining) == 1:
        return remaining[0], False
    if len(remaining) > 1:
        return None, True
    return None, False


def _extract_rc(text: str) -> tuple[float | None, bool]:
    """Return an explicitly stated R&C/eligible-charge amount and lookup flag.

    Presence of R&C language alone is not evidence that the smallest dollar in
    the block is the R&C value.
    """
    if not _RC_TERM.search(text):
        return None, False
    values: list[float] = []
    for pattern in _RC_FIXED:
        values.extend(_money_values(pattern.findall(text)))
    values = _unique(values)
    if len(values) == 1:
        return values[0], False
    return None, True


def _field_evidence(field: str, excerpt: str, confidence: str) -> FieldEvidence:
    return FieldEvidence(
        field=field,
        source_kind="plan_text",
        excerpt=excerpt[:1200],
        confidence=confidence,
    )


def parse_benefits_text(text: str) -> ParseResult:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    benefits: list[BenefitRule] = []
    warnings: list[str] = []

    for category in CATEGORIES:
        blocks = _blocks(lines, category.keywords)
        if not blocks:
            continue
        combined = " | ".join(dict.fromkeys(blocks))
        lower = combined.lower()
        pct_match = _PERCENT.search(combined)
        coverage = float(pct_match.group(1)) if pct_match else None
        period_kind, period_months = _period(combined)
        maximum, maximum_ambiguous = _maximum(combined, period_kind)
        visits_match = _VISITS.search(combined)
        visit_limit = int(visits_match.group(1)) if visits_match else None
        per_visit_amounts = _per_visit_amounts(combined)
        rc_cap, rc_lookup_required = _extract_rc(combined)
        referral = True if "referral required" in lower or "physician referral" in lower else None
        prescription = True if "prescription required" in lower else None

        notes: list[str] = []
        manual_review_required = False
        field_evidence: list[FieldEvidence] = []
        limits: list[BenefitLimit] = []
        eligible_charge_rules: list[EligibleChargeRule] = []

        if coverage is None:
            notes.append("Coverage percentage was not confidently extracted.")
        else:
            field_evidence.append(_field_evidence("coverage_percent", combined, "high"))

        if period_kind == "annual_unspecified":
            notes.append("Text describes an annual period but does not establish the reset anchor; manual review is required.")
            manual_review_required = True
            field_evidence.append(_field_evidence("period_kind", combined, "low"))
        elif period_kind != "unknown":
            field_evidence.append(_field_evidence("period_kind", combined, "high"))

        if maximum is None:
            notes.append("Benefit maximum was not confidently bound to one semantic amount for a recognized period.")
            if maximum_ambiguous:
                notes.append("Multiple monetary values remain semantically ambiguous; numeric magnitude was not used to choose a maximum.")
                manual_review_required = True
        else:
            field_evidence.append(_field_evidence("maximum_amount", combined, "medium"))
            scope = "shared_pool" if "combined maximum" in lower else "per_category"
            limits.append(
                BenefitLimit(
                    limit_type="currency",
                    amount=maximum,
                    basis="unknown",
                    scope=scope,
                    period_kind=period_kind,
                    period_months=period_months,
                    evidence=[_field_evidence("limits", combined, "medium")],
                )
            )

        if period_kind == "rolling_months":
            notes.append(f"Maximum appears to use a rolling {period_months}-month period, not an annual limit.")

        if visit_limit is not None:
            field_evidence.append(_field_evidence("visit_limit", combined, "high"))
            limits.append(
                BenefitLimit(
                    limit_type="visits",
                    amount=float(visit_limit),
                    basis="visit_count",
                    scope="per_category",
                    period_kind=period_kind,
                    period_months=period_months,
                    evidence=[_field_evidence("limits", combined, "high")],
                )
            )

        for per_visit_amount in per_visit_amounts:
            limits.append(
                BenefitLimit(
                    limit_type="currency",
                    amount=per_visit_amount,
                    basis="unknown",
                    scope="per_visit",
                    period_kind="unknown",
                    evidence=[_field_evidence("limits", combined, "medium")],
                )
            )

        if _RC_TERM.search(combined):
            eligible_charge_rules.append(
                EligibleChargeRule(
                    method="reasonable_customary",
                    fixed_amount=rc_cap,
                    external_lookup_required=rc_lookup_required,
                    evidence=[_field_evidence("eligible_charge_rules", combined, "medium" if rc_lookup_required else "high")],
                )
            )
            field_evidence.append(_field_evidence("reasonable_customary_cap", combined, "low" if rc_lookup_required else "high"))
            if rc_lookup_required:
                notes.append("R&C/eligible-charge language is present but no exact service-context amount was established; external lookup/manual review is required.")
                manual_review_required = True

        if "combined maximum" in lower:
            notes.append("Text may describe a shared/combined pool; beta requires human review before optimization.")
            manual_review_required = True

        if referral is not None:
            field_evidence.append(_field_evidence("requires_referral", combined, "medium"))
        if prescription is not None:
            field_evidence.append(_field_evidence("requires_prescription", combined, "medium"))

        confidence = "low"
        if coverage is not None and (maximum is not None or visit_limit is not None):
            confidence = "medium"
        if (
            coverage is not None
            and maximum is not None
            and period_kind not in ("unknown", "annual_unspecified")
            and not manual_review_required
        ):
            confidence = "high"

        benefits.append(
            BenefitRule(
                category=category.name,
                coverage_percent=coverage,
                maximum_amount=maximum,
                period_kind=period_kind,
                period_months=period_months,
                visit_limit=visit_limit,
                reasonable_customary_cap=rc_cap,
                requires_referral=referral,
                requires_prescription=prescription,
                confidence=confidence,
                evidence_excerpt=combined[:1200],
                field_evidence=field_evidence,
                limits=limits,
                eligible_charge_rules=eligible_charge_rules,
                manual_review_required=manual_review_required,
                notes=notes,
            )
        )

    if not benefits:
        warnings.append("No supported benefit categories were found. Review the document manually or supply clearer plan text.")
    warnings.append("Beta extraction is decision support, not an insurer coverage guarantee. Material ambiguity must be reviewed against the authoritative plan.")
    return ParseResult(benefits=benefits, warnings=warnings)
