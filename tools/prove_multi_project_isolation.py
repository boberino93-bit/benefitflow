from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sqlite3
import tempfile
import time
from pathlib import Path
from queue import Empty

from benefitflow_beta.coordination import AgentIdentity, AuthorizationError, ConflictError, ProjectMode
from benefitflow_beta.durable_coordination import DurableCoordinationStore


def _manager(instance_id: str) -> AgentIdentity:
    return AgentIdentity("benefitflow", "manager-prover", instance_id, "MANAGER")


def _primary(instance_id: str = "primary-prover") -> AgentIdentity:
    return AgentIdentity("benefitflow", "primary-prover", instance_id, "PRIMARY")


def _benefitflow_duplicate_worker(database: str, index: int, queue: mp.Queue) -> None:
    store = DurableCoordinationStore(database)
    try:
        result = store.apply_state_mutation(
            actor=_manager(f"bf-{index}"),
            resource_id="shared-task-id",
            expected_version=0,
            value={"winner": index},
            correlation_id="prove-correlation",
            causation_id="prove-human",
            idempotency_key="shared-idempotency-key",
            outbox_topic="prove.state.changed",
        )
        queue.put({"status": "ok", "duplicate": result["duplicate"], "version": result["version"]})
    except Exception as exc:
        queue.put({"status": "error", "type": type(exc).__name__, "message": str(exc)})


def _project_c_mutation(database: str, value: int) -> None:
    """Disposable foreign-project fixture; never uses BenefitFlow runtime authority."""
    conn = sqlite3.connect(database, timeout=30.0, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("BEGIN IMMEDIATE")
        now = "2026-10-04T00:00:00+00:00"
        row = conn.execute(
            "SELECT version FROM versioned_state WHERE project_id='project-c' AND resource_id='shared-task-id'"
        ).fetchone()
        version = 1 if row is None else int(row[0]) + 1
        conn.execute(
            """
            INSERT INTO versioned_state(project_id, resource_id, version, value_json, updated_at)
            VALUES('project-c', 'shared-task-id', ?, ?, ?)
            ON CONFLICT(project_id, resource_id)
            DO UPDATE SET version=excluded.version, value_json=excluded.value_json, updated_at=excluded.updated_at
            """,
            (version, json.dumps({"project": "c", "value": value}), now),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO idempotency(
                project_id, idempotency_key, owner_instance_id, status,
                result_json, reserved_at, expires_at, updated_at
            ) VALUES(
                'project-c', 'shared-idempotency-key', 'project-c-fixture', 'COMPLETE',
                '{"project":"c"}', ?, '2099-01-01T00:00:00+00:00', ?
            )
            """,
            (now, now),
        )
        conn.execute("COMMIT")
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _crash_after_lease(database: str) -> None:
    store = DurableCoordinationStore(database)
    store.claim_lease(
        actor=_manager("crashed-holder"),
        resource_id="recoverable-lease",
        ttl_seconds=1,
        correlation_id="lease-correlation",
        causation_id="lease-cause",
        idempotency_key="crash-lease-claim",
    )


def prove(database: str) -> dict:
    store = DurableCoordinationStore(database)
    queue: mp.Queue = mp.Queue()
    workers = [mp.Process(target=_benefitflow_duplicate_worker, args=(database, index, queue)) for index in range(8)]
    for worker in workers: worker.start()
    for worker in workers:
        worker.join(15)
        if worker.exitcode != 0: raise RuntimeError(f"BenefitFlow proving worker failed: {worker.exitcode}")
    results = []
    for _ in workers:
        try: results.append(queue.get(timeout=3))
        except Empty as exc: raise RuntimeError("missing BenefitFlow worker result") from exc
    if any(item["status"] != "ok" for item in results): raise RuntimeError(f"BenefitFlow duplicate proving failure: {results}")
    if sum(not item["duplicate"] for item in results) != 1: raise RuntimeError(f"expected exactly one effective BenefitFlow mutation: {results}")
    if sum(item["duplicate"] for item in results) != 7: raise RuntimeError(f"expected seven BenefitFlow safe replays: {results}")

    project_c = mp.Process(target=_project_c_mutation, args=(database, 1)); project_c.start(); project_c.join(15)
    if project_c.exitcode != 0: raise RuntimeError("Project-C fixture mutation failed")
    bf_version, bf_value = store.read_state("shared-task-id")
    foreign_counts = store.foreign_row_counts()
    if bf_version != 1 or foreign_counts["versioned_state"] != 1: raise RuntimeError("project-qualified state collision detected")

    crashed = mp.Process(target=_crash_after_lease, args=(database,)); crashed.start(); crashed.join(15)
    if crashed.exitcode != 0: raise RuntimeError("crash/lease fixture failed")
    early_conflict = False
    try:
        store.claim_lease(actor=_manager("recovery-holder"),resource_id="recoverable-lease",ttl_seconds=5,correlation_id="recovery-early",causation_id="recovery-cause",idempotency_key="recover-lease-too-early")
    except ConflictError: early_conflict = True
    if not early_conflict: raise RuntimeError("active crashed-instance lease was stolen before TTL")
    time.sleep(1.1)
    recovered = store.claim_lease(actor=_manager("recovery-holder"),resource_id="recoverable-lease",ttl_seconds=5,correlation_id="recovery-late",causation_id="recovery-cause",idempotency_key="recover-lease-after-expiry")

    primary = _primary(); mode, control_version = store.mode()
    if mode != ProjectMode.ACTIVE: raise RuntimeError("BenefitFlow did not begin proving scenario ACTIVE")
    store.set_project_mode(requester=primary,mode=ProjectMode.PAUSED,expected_version=control_version,human_approved=True,correlation_id="pause-correlation",causation_id="explicit-human-proving-approval",idempotency_key="prove-pause")
    pause_blocked = False
    try:
        store.apply_state_mutation(actor=primary,resource_id="pause-probe",expected_version=0,value={"should":"not-write"},correlation_id="pause-write-correlation",causation_id="pause-cause",idempotency_key="pause-write")
    except AuthorizationError: pause_blocked = True
    if not pause_blocked: raise RuntimeError("BenefitFlow pause did not block BenefitFlow mutation")

    project_c_during_pause = mp.Process(target=_project_c_mutation, args=(database, 2)); project_c_during_pause.start(); project_c_during_pause.join(15)
    if project_c_during_pause.exitcode != 0: raise RuntimeError("Project-C was incorrectly coupled to BenefitFlow pause")
    _, paused_version = store.mode()
    store.set_project_mode(requester=primary,mode=ProjectMode.ACTIVE,expected_version=paused_version,human_approved=True,correlation_id="resume-correlation",causation_id="explicit-human-proving-approval",idempotency_key="prove-resume")

    restarted = DurableCoordinationStore(database)
    replay = restarted.apply_state_mutation(actor=_manager("post-restart"),resource_id="shared-task-id",expected_version=0,value={"must":"not-overwrite"},correlation_id="prove-correlation",causation_id="prove-human",idempotency_key="shared-idempotency-key")
    if replay["duplicate"] is not True: raise RuntimeError("idempotency did not survive process restart")
    integrity = restarted.verify_integrity()
    return {
        "schema":"benefitflow/multi-project-proving-result/v1","project_id":"benefitflow",
        "benefitflow_effective_mutations":1,"benefitflow_safe_replays":7,
        "benefitflow_state_version":bf_version,"benefitflow_state":bf_value,
        "foreign_project_rows_visible_to_diagnostics_only":restarted.foreign_row_counts(),
        "crashed_lease_recovered_by":recovered["holder_instance_id"],
        "benefitflow_pause_blocked_local_mutation":pause_blocked,
        "project_c_progressed_during_benefitflow_pause":True,
        "restart_idempotency_replay":replay["duplicate"],"integrity":integrity,"valid":True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BenefitFlow + disposable Project-C concurrency/isolation proving scenario.")
    parser.add_argument("--database", help="Optional SQLite database path; a temporary database is used by default.")
    args = parser.parse_args()
    if args.database: result = prove(args.database)
    else:
        with tempfile.TemporaryDirectory() as temp_dir: result = prove(str(Path(temp_dir) / "benefitflow-proving.sqlite"))
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__": main()
