import json
import pytest

from benefitflow_beta.models import BookingProposalRequest
from benefitflow_beta.workflow import approve_proposal, create_proposal, verify_provider


def request():
    return BookingProposalRequest(
        provider_id="demo-physio-1",
        category="physiotherapy",
        preferred_window="Tuesday afternoon",
        insurer_name="Example Insurer",
        plan_number="12345678",
        member_id="ABCDEFGH",
    )


def test_proposal_requires_prior_provider_verification(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    with pytest.raises(ValueError):
        create_proposal(request())


def test_proposal_does_not_persist_raw_identifiers(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    record = storage.get(f"proposal:{proposal.proposal_id}")
    serialized = json.dumps(record)
    assert "12345678" not in serialized
    assert "ABCDEFGH" not in serialized
    assert record["identifier_tails"]["plan_number_tail"] == "5678"
    assert record["identifier_tails"]["member_id_tail"] == "EFGH"


def test_approval_decision_is_final_and_replay_safe(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    declined = approve_proposal(proposal.proposal_id, False)
    assert declined.status == "DECLINED"
    with pytest.raises(ValueError):
        approve_proposal(proposal.proposal_id, True)


def test_approved_proposal_releases_only_demo_transaction_handoff(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    approved = approve_proposal(proposal.proposal_id, True)
    assert approved.status == "READY_FOR_TRANSACTION_ADAPTER"
    assert "no live external action" in approved.transaction_script.lower()
    record = storage.get(f"proposal:{proposal.proposal_id}")
    assert record["approval"]["decision"] == "APPROVED"
    assert record["approval"]["live_external_action_allowed"] is False
