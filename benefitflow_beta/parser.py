from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

from pypdf import PdfReader

from .models import BenefitRule, ParseResult


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


def _period(text: str) -> tuple[str, int | None]:
    lower = text.lower()
    if "lifetime" in lower:
        return "lifetime", None
    m = _MONTH_PERIOD.search(lower)
    if m:
        return "rolling_months", int(m.group(1))
    if "calendar year" in lower:
        return "calendar_year", 12
    if "benefit year" in lower or "per year" in lower or "annual" in lower or "annually" in lower:
        return "benefit_year", 12
    return "unknown", None


def _maximum(text: str, period_kind: str) -> float | None:
    if period_kind == "unknown":
        return None
    amounts = [float(x.replace(",", "")) for x in _MONEY.findall(text)]
    return max(amounts) if amounts else None


def _extract_rc(text: str) -> float | None:
    lower = text.lower()
    if not any(t in lower for t in ("reasonable and customary", "reasonable & customary", "r&c", "eligible charge")):
        return None
    amounts = [float(x.replace(",", "")) for x in _MONEY.findall(text)]
    return min(amounts) if amounts else None


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
        maximum = _maximum(combined, period_kind)
        visits_match = _VISITS.search(combined)
        visit_limit = int(visits_match.group(1)) if visits_match else None
        rc_cap = _extract_rc(combined)
        referral = True if "referral required" in lower or "physician referral" in lower else None
        prescription = True if "prescription required" in lower else None

        notes: list[str] = []
        if coverage is None:
            notes.append("Coverage percentage was not confidently extracted.")
        if maximum is None:
            notes.append("Benefit maximum was not confidently extracted for a recognized period.")
        if period_kind == "rolling_months":
            notes.append(f"Maximum appears to use a rolling {period_months}-month period, not an annual limit.")
        if "combined maximum" in lower or "combined maximum" in lower:
            notes.append("Text may describe a shared/combined pool; beta requires human review before optimization.")

        confidence = "low"
        if coverage is not None and (maximum is not None or visit_limit is not None):
            confidence = "medium"
        if coverage is not None and maximum is not None and period_kind != "unknown":
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
                notes=notes,
            )
        )

    if not benefits:
        warnings.append("No supported benefit categories were found. Review the document manually or supply clearer plan text.")
    warnings.append("Beta extraction is decision support, not an insurer coverage guarantee. Material ambiguity must be reviewed against the authoritative plan.")
    return ParseResult(benefits=benefits, warnings=warnings)
