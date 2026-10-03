from __future__ import annotations

from datetime import datetime, timezone
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


def _tail(value: str) -> str:
    return value[-4:] if value else ""


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
    allowed_disclosures = []
    if req.plan_number:
        allowed_disclosures.append("plan_number")
    if req.member_id:
        allowed_disclosures.append("member_id")
    put(
        f"proposal:{proposal_id}",
        {
            "proposal": proposal.model_dump(mode="json"),
            "identifier_tails": {
                "plan_number_tail": _tail(req.plan_number),
                "member_id_tail": _tail(req.member_id),
            },
            "requested_disclosures": allowed_disclosures,
            "approval": None,
        },
    )
    return proposal


def _approved_result(proposal: BookingProposal, record: dict) -> BookingResult:
    tails = record.get("identifier_tails", {})
    plan_tail = tails.get("plan_number_tail") or "N/A"
    member_tail = tails.get("member_id_tail") or "N/A"
    approval = record.get("approval") or {}
    script = f"""DEMO TRANSACTION SCOPE — no live external action is authorized by this build.

Arrange a {proposal.category} appointment with {proposal.provider.name} within {proposal.preferred_window}. The verified synthetic price is ${proposal.expected_cost:.2f} and direct-billing status is '{proposal.verification.direct_billing}'.

Authorization {approval.get('authorization_id', 'N/A')} permits only these disclosure categories: {', '.join(approval.get('allowed_disclosures', [])) or 'none'}.

If a production adapter were enabled later, it would have to reconfirm the clinic/service and necessity before retrieving secrets from a dedicated secret store. The demo retains only masked tails: plan ****{plan_tail}; member ****{member_tail}.

Any material change to provider, practitioner, service, price, cancellation terms, appointment window, disclosure category, payment, or claim submission requires fresh user authorization."""
    return BookingResult(
        proposal_id=proposal.proposal_id,
        status="READY_FOR_TRANSACTION_ADAPTER",
        next_action="Alpha 0.4 may execute only the local synthetic transaction simulator. Live adapters remain blocked by the P0 gate.",
        transaction_script=script,
    )


def approve_proposal(proposal_id: str, approved: bool) -> BookingResult:
    record = get(f"proposal:{proposal_id}")
    if record is None:
        raise KeyError("proposal not found")
    proposal = BookingProposal.model_validate(record["proposal"])

    existing = record.get("approval")
    if existing is not None:
        existing_approved = existing.get("decision") == "APPROVED"
        if existing_approved != approved:
            raise ValueError("approval decision is final for this proposal; create a new proposal for a different decision")
        if approved:
            return _approved_result(proposal, record)
        return BookingResult(proposal_id=proposal_id, status="DECLINED", next_action="No external action is authorized.")

    if not approved:
        record["approval"] = {
            "decision": "DECLINED",
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "authorization_id": None,
            "allowed_disclosures": [],
        }
        put(f"proposal:{proposal_id}", record)
        return BookingResult(proposal_id=proposal_id, status="DECLINED", next_action="No external action is authorized.")

    record["approval"] = {
        "decision": "APPROVED",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "authorization_id": "auth_" + secrets.token_urlsafe(8),
        "allowed_disclosures": record.get("requested_disclosures", []),
        "purpose": "synthetic appointment-coordination proof of concept",
        "recipient": proposal.provider.provider_id,
        "expires_when": "proposal scope materially changes",
        "live_external_action_allowed": False,
    }
    put(f"proposal:{proposal_id}", record)
    return _approved_result(proposal, record)
