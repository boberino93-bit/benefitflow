from __future__ import annotations

from datetime import datetime, timezone

from .models import Provider, ProviderVerification

PROVIDERS = [
    Provider(provider_id="demo-physio-1", name="Harbour Demo Physiotherapy", category="physiotherapy", city="Victoria, BC (demo)", phone="+1-555-0101", booking_channel="phone"),
    Provider(provider_id="demo-rmt-1", name="Cedar Demo Massage Therapy", category="massage therapy", city="Victoria, BC (demo)", phone="+1-555-0102", booking_channel="web"),
    Provider(provider_id="demo-psych-1", name="Northstar Demo Psychology", category="psychology", city="Victoria, BC (demo)", phone="+1-555-0103", booking_channel="phone"),
    Provider(provider_id="demo-chiro-1", name="Summit Demo Chiropractic", category="chiropractic", city="Victoria, BC (demo)", phone="+1-555-0104", booking_channel="phone"),
]


def list_providers(category: str | None = None) -> list[Provider]:
    if not category:
        return PROVIDERS
    key = category.lower()
    return [p for p in PROVIDERS if p.category.lower() == key]


def get_provider(provider_id: str) -> Provider | None:
    return next((p for p in PROVIDERS if p.provider_id == provider_id), None)


def get_provider_evidence(provider_id: str) -> dict:
    provider = get_provider(provider_id)
    if provider is None:
        raise KeyError("provider not found")
    now = datetime.now(timezone.utc).isoformat()
    return {
        "provider_id": provider.provider_id,
        "synthetic": True,
        "assertions": [
            {"field": "identity", "value": provider.name, "source": "synthetic demo registry", "freshness": "demo-static", "confidence": "high", "automation_authorized": True},
            {"field": "service", "value": provider.category, "source": "synthetic clinic profile", "freshness": "demo-static", "confidence": "high", "automation_authorized": True},
            {"field": "location", "value": provider.city, "source": "synthetic clinic profile", "freshness": "demo-static", "confidence": "high", "automation_authorized": True},
            {"field": "booking_channel", "value": provider.booking_channel, "source": "synthetic clinic capability record", "freshness": "demo-static", "confidence": "high", "automation_authorized": True},
            {"field": "availability", "value": "must be verified before proposal", "source": "synthetic verification adapter", "freshness": "transaction-time", "confidence": "unknown until verified", "automation_authorized": True},
            {"field": "direct_billing", "value": "must be verified per insurer", "source": "synthetic verification adapter", "freshness": "transaction-time", "confidence": "unknown until verified", "automation_authorized": True},
        ],
        "observed_at": now,
        "note": "These assertions demonstrate field-level provenance/freshness. Production sources require separate authorization and terms review.",
    }


def simulate_verification(provider_id: str, insurer_name: str) -> ProviderVerification:
    provider = get_provider(provider_id)
    if provider is None:
        raise KeyError("provider not found")
    price = {"physiotherapy": 115.0, "massage therapy": 130.0, "psychology": 225.0, "chiropractic": 80.0}.get(provider.category, 120.0)
    return ProviderVerification(
        provider_id=provider.provider_id,
        insurer_name=insurer_name,
        accepting_new_patients=True,
        current_price=price,
        direct_billing="confirmed" if insurer_name else "unknown",
        required_profile_fields=["plan number", "member/certificate ID"] if insurer_name else [],
        referral_required=False,
        prescription_required=False,
        cancellation_policy="Synthetic demo: 24 hours notice.",
        verified_at=datetime.now(timezone.utc),
        evidence_note="Synthetic transaction-time verification. No clinic or insurer was contacted.",
    )
