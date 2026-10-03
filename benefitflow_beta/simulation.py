from __future__ import annotations

from datetime import datetime, timezone
import secrets

from .storage import get, put

SCENARIOS = {
    "confirmed",
    "waitlisted",
    "retryable_failure",
    "ambiguous_after_send",
    "rejected",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(seq: int, state: str, note: str) -> dict:
    return {"seq": seq, "state": state, "timestamp": _now(), "note": note}


def simulate_transaction(proposal_id: str, scenario: str = "confirmed") -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"unsupported demo scenario: {scenario}")

    record = get(f"proposal:{proposal_id}")
    if record is None:
        raise KeyError("proposal not found")

    approval = record.get("approval")
    if not approval or approval.get("decision") != "APPROVED":
        raise ValueError("an active approved authorization is required before the demo transaction can execute")

    existing = get(f"transaction:{proposal_id}")
    if existing is not None:
        return existing

    transaction_id = "tx_" + secrets.token_urlsafe(8)
    operation_id = "op_" + secrets.token_urlsafe(7)
    attempt_id = "at_" + secrets.token_urlsafe(7)
    events = [
        _event(1, "READY_FOR_EXECUTION", "User approval and scoped disclosure authorization are present."),
        _event(2, "EXECUTING", "Synthetic adapter attempt started. No external system was contacted."),
    ]

    if scenario == "confirmed":
        events.extend([
            _event(3, "REQUEST_SUBMITTED", "Synthetic booking request accepted by the mock adapter."),
            _event(4, "AWAITING_EXTERNAL_CONFIRMATION", "The mock adapter is waiting for authoritative confirmation."),
            _event(5, "CONFIRMED_BOOKED", "Synthetic provider confirmation received and validated."),
            _event(6, "CALENDAR_PROJECTED", "Demo calendar projection created after confirmation."),
        ])
        outcome = "CONFIRMED_BOOKED"
        calendar_projection = {
            "status": "PROJECTED_DEMO_ONLY",
            "title": f"{record['proposal']['category'].title()} — {record['proposal']['provider']['name']}",
            "window": record["proposal"]["preferred_window"],
        }
    elif scenario == "waitlisted":
        events.extend([
            _event(3, "REQUEST_SUBMITTED", "Synthetic request submitted."),
            _event(4, "WAITLISTED", "Provider has not confirmed an appointment; this is not a booking."),
        ])
        outcome = "WAITLISTED"
        calendar_projection = None
    elif scenario == "retryable_failure":
        events.append(_event(3, "FAILED_RETRYABLE", "Transport failed before any business-side action could occur."))
        outcome = "FAILED_RETRYABLE"
        calendar_projection = None
    elif scenario == "ambiguous_after_send":
        events.extend([
            _event(3, "REQUEST_SUBMITTED", "Synthetic request may have reached the provider."),
            _event(4, "RECONCILIATION_REQUIRED", "Outcome is ambiguous. Blind retry is blocked to avoid duplicate booking."),
        ])
        outcome = "RECONCILIATION_REQUIRED"
        calendar_projection = None
    else:
        events.extend([
            _event(3, "REQUEST_SUBMITTED", "Synthetic request submitted."),
            _event(4, "REJECTED", "Provider rejected the requested booking."),
        ])
        outcome = "REJECTED"
        calendar_projection = None

    transaction = {
        "transaction_id": transaction_id,
        "operation_id": operation_id,
        "attempt_id": attempt_id,
        "proposal_id": proposal_id,
        "scenario": scenario,
        "outcome": outcome,
        "synthetic": True,
        "live_external_action": False,
        "events": events,
        "calendar_projection": calendar_projection,
        "authorization_id": approval.get("authorization_id"),
        "allowed_disclosures": approval.get("allowed_disclosures", []),
    }
    put(f"transaction:{proposal_id}", transaction)
    return transaction


def get_transaction(proposal_id: str) -> dict:
    transaction = get(f"transaction:{proposal_id}")
    if transaction is None:
        raise KeyError("transaction not found")
    return transaction


def get_audit(proposal_id: str) -> dict:
    record = get(f"proposal:{proposal_id}")
    if record is None:
        raise KeyError("proposal not found")
    return {
        "proposal_id": proposal_id,
        "proposal": record.get("proposal"),
        "approval": record.get("approval"),
        "transaction": get(f"transaction:{proposal_id}"),
        "sensitive_values_retained": False,
        "note": "Alpha 0.4 demo audit contains masked identifiers/categories only; no external transaction occurred.",
    }
