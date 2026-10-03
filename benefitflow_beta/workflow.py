from __future__ import annotations

import secrets

from .models import BookingProposal, BookingProposalRequest, BookingResult, ProviderVerification
from .providers import get_provider, simulate_verification
from .storage import get, put


def _mask(value: str) -> str:
    if not value:
        return "not provided"
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


def verify_provider(provider_id: str, insurer_name: str) -> ProviderVerification:
    verification = simulate_verification(provider_id, insurer_name)
    put(f"verification:{provider_id}:{insurer_name.lower()}", verification.model_dump(mode="json"))
    return verification


def create_proposal(req: BookingProposalRequest) -> BookingProposal:
    provider = get_provider(req.provider_id)
    if provider is None:
        raise KeyError("provider not found")
    stored = get(f"verification:{req.provider_id}:{req.insurer_name.lower()}")
    if stored is None:
        raise ValueError("provider must be verified for this insurer before a booking proposal can be created")
    verification = ProviderVerification.model_validate(stored)
    if verification.accepting_new_patients is not True or verification.current_price is None:
        raise ValueError("provider verification is incomplete")

    proposal_id = "bp_" + secrets.token_urlsafe(8)
    proposal = BookingProposal(
        proposal_id=proposal_id,
        provider=provider,
        verification=verification,
        category=req.category,
        preferred_window=req.preferred_window,
        expected_cost=verification.current_price,
        insurer_name=req.insurer_name,
        plan_number_masked=_mask(req.plan_number),
        member_id_masked=_mask(req.member_id),
    )
    put(f"proposal:{proposal_id}", {"proposal": proposal.model_dump(mode="json"), "sensitive": {"plan_number": req.plan_number, "member_id": req.member_id}})
    return proposal


def approve_proposal(proposal_id: str, approved: bool) -> BookingResult:
    record = get(f"proposal:{proposal_id}")
    if record is None:
        raise KeyError("proposal not found")
    proposal = BookingProposal.model_validate(record["proposal"])
    if not approved:
        return BookingResult(proposal_id=proposal_id, status="DECLINED", next_action="No external action is authorized.")

    sensitive = record.get("sensitive", {})
    plan_tail = sensitive.get("plan_number", "")[-4:] or "N/A"
    member_tail = sensitive.get("member_id", "")[-4:] or "N/A"
    script = f"""Hello, I’m an automated scheduling assistant acting with the member's approval to arrange a {proposal.category} appointment with {proposal.provider.name}.

The clinic verification on file indicates a current price of ${proposal.expected_cost:.2f}, direct billing status '{proposal.verification.direct_billing}', and a requested window of {proposal.preferred_window}.

Before disclosing identifiers, reconfirm that the clinic needs them for direct-billing profile setup and that the practitioner/service remains the one verified. The approved stored plan number ends in {plan_tail}; the member/certificate ID ends in {member_tail}.

Do not accept a materially different provider, practitioner, service, price, cancellation condition, or appointment window without returning to the user for fresh approval. Do not pay a deposit or submit a claim without separate authorization."""
    return BookingResult(
        proposal_id=proposal_id,
        status="READY_FOR_TRANSACTION_ADAPTER",
        next_action="Beta stops at the transaction adapter boundary. A production voice/web adapter may act only within this approved scope.",
        transaction_script=script,
    )
