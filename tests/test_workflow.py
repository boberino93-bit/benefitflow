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


def test_approval_gate_releases_only_transaction_handoff(tmp_path, monkeypatch):
    import benefitflow_beta.storage as storage
    monkeypatch.setattr(storage, "_DB", tmp_path / "state.sqlite3")
    verify_provider("demo-physio-1", "Example Insurer")
    proposal = create_proposal(request())
    assert proposal.status == "AWAITING_USER_APPROVAL"
    declined = approve_proposal(proposal.proposal_id, False)
    assert declined.status == "DECLINED"
    approved = approve_proposal(proposal.proposal_id, True)
    assert approved.status == "READY_FOR_TRANSACTION_ADAPTER"
    assert "Do not accept a materially different" in approved.transaction_script
