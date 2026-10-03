import pytest

from benefitflow_beta.models import BookingProposalRequest
from benefitflow_beta.simulation import simulate_transaction
from benefitflow_beta.workflow import approve_proposal, create_proposal, verify_provider


def request():
    return BookingProposalRequest(
        provider_id="demo-physio-1",
        category="physiotherapy",
        preferred_window="Tuesday afternoon",
        insurer_name="Example Insurer",
        plan_number="DEMO-PLAN-0001",
        member_id="DEMO-MEMBER-0001",
    )


def approved_proposal(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    approve_proposal(proposal.proposal_id, True)
    return proposal


def test_confirmed_scenario_requires_authoritative_confirmation_before_calendar(tmp_path, monkeypatch):
    proposal = approved_proposal(tmp_path, monkeypatch)
    tx = simulate_transaction(proposal.proposal_id, "confirmed")
    states = [event["state"] for event in tx["events"]]
    assert states.index("CONFIRMED_BOOKED") < states.index("CALENDAR_PROJECTED")
    assert tx["outcome"] == "CONFIRMED_BOOKED"
    assert tx["live_external_action"] is False
    assert tx["calendar_projection"]["status"] == "PROJECTED_DEMO_ONLY"


def test_ambiguous_after_send_blocks_blind_retry(tmp_path, monkeypatch):
    proposal = approved_proposal(tmp_path, monkeypatch)
    tx = simulate_transaction(proposal.proposal_id, "ambiguous_after_send")
    states = [event["state"] for event in tx["events"]]
    assert "REQUEST_SUBMITTED" in states
    assert "RECONCILIATION_REQUIRED" in states
    assert "CONFIRMED_BOOKED" not in states
    assert tx["calendar_projection"] is None


def test_waitlist_is_not_counted_as_booking(tmp_path, monkeypatch):
    proposal = approved_proposal(tmp_path, monkeypatch)
    tx = simulate_transaction(proposal.proposal_id, "waitlisted")
    assert tx["outcome"] == "WAITLISTED"
    assert all(event["state"] != "CONFIRMED_BOOKED" for event in tx["events"])


def test_demo_execution_is_idempotent_for_same_proposal(tmp_path, monkeypatch):
    proposal = approved_proposal(tmp_path, monkeypatch)
    first = simulate_transaction(proposal.proposal_id, "confirmed")
    second = simulate_transaction(proposal.proposal_id, "rejected")
    assert second["transaction_id"] == first["transaction_id"]
    assert second["outcome"] == first["outcome"]


def test_declined_proposal_cannot_execute(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    approve_proposal(proposal.proposal_id, False)
    with pytest.raises(ValueError):
        simulate_transaction(proposal.proposal_id, "confirmed")
