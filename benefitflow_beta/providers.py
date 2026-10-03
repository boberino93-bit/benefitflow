from __future__ import annotations

from datetime import datetime, timezone

from .models import Provider, ProviderVerification

PROVIDERS = [
    Provider(provider_id="demo-physio-1", name="Harbour Demo Physiotherapy", category="physiotherapy", city="Example City, BC", phone="+1-555-0101", booking_channel="phone"),
    Provider(provider_id="demo-rmt-1", name="Cedar Demo Massage Therapy", category="massage therapy", city="Example City, BC", phone="+1-555-0102", booking_channel="web"),
    Provider(provider_id="demo-psych-1", name="Northstar Demo Psychology", category="psychology", city="Example City, BC", phone="+1-555-0103", booking_channel="phone"),
    Provider(provider_id="demo-chiro-1", name="Summit Demo Chiropractic", category="chiropractic", city="Example City, BC", phone="+1-555-0104", booking_channel="phone"),
]


def list_providers(category: str | None = None) -> list[Provider]:
    if not category:
        return PROVIDERS
    key = category.lower()
    return [p for p in PROVIDERS if p.category.lower() == key]


def get_provider(provider_id: str) -> Provider | None:
    return next((p for p in PROVIDERS if p.provider_id == provider_id), None)


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
        cancellation_policy="Synthetic beta: 24 hours notice.",
        verified_at=datetime.now(timezone.utc),
        evidence_note="Synthetic verification record. Production must replace this with current provider confirmation evidence.",
    )
