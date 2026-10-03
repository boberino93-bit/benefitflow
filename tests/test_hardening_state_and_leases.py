from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import pytest

from benefitflow_coordination.identity import make_primary_binding
from benefitflow_coordination.leases import LeaseConflict, LeaseStore
from benefitflow_coordination.state import AtomicVersionedState, StaleWriteError


def test_compare_and_set_rejects_stale_write(tmp_path):
    binding = make_primary_binding(tmp_path)
    store = AtomicVersionedState(tmp_path / "state", binding)
    first = store.compare_and_set("task-001", expected_version=0, value={"status": "OPEN"})
    assert first["version"] == 1
    with pytest.raises(StaleWriteError):
        store.compare_and_set("task-001", expected_version=0, value={"status": "DONE"})


def test_atomic_lease_allows_one_holder(tmp_path):
    root = tmp_path
    bindings = [make_primary_binding(root, agent_id=f"worker-{i}") for i in range(8)]
    wins = []
    conflicts = []

    def claim(binding):
        try:
            lease = LeaseStore(root / "leases", binding).claim("task-001", ttl_seconds=60)
            wins.append(lease)
        except LeaseConflict:
            conflicts.append(binding.agent_id)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(claim, bindings))
    assert len(wins) == 1
    assert len(conflicts) == 7


def test_expired_lease_is_recoverable(tmp_path):
    first = make_primary_binding(tmp_path, agent_id="worker-a")
    store_a = LeaseStore(tmp_path / "leases", first)
    old = datetime.now(timezone.utc) - timedelta(minutes=5)
    store_a.claim("task-001", ttl_seconds=1, now=old)

    second = make_primary_binding(tmp_path, agent_id="worker-b")
    recovered = LeaseStore(tmp_path / "leases", second).claim("task-001", ttl_seconds=60)
    assert recovered["holder_agent_instance_id"] == second.agent_instance_id
