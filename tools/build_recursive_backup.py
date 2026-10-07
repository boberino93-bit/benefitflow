from __future__ import annotations
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"

IDENTITY_ARTIFACTS = [
    ROOT / "AGENT_BOOTSTRAP.json",
    ROOT / "AGENT_BOOTSTRAP.md",
    ROOT / "AUTHORITY_SECURITY_OVERLAY.json",
    ROOT / "NEW_PROJECT_BOOTSTRAP.json",
    ROOT / "REPOSITORY_BOOTSTRAP.md",
    BUS / "PROJECT_SCOPE_SELECTION_GATE_V1.md",
    BUS / "control/PROJECT_IDENTITY_LOCK.json",
    BUS / "control/PROJECT_MUTATION_AUTHORITY_V1.json",
    BUS / "control/PROJECT_SCOPE_BINDING.json",
    BUS / "control/GITHUB_REPOSITORY_BINDING.json",
    BUS / "control/PROJECT_MANIFEST.json",
]

REQUIRED = [
    ROOT / "AGENT_BOOTSTRAP.json",
    ROOT / "AGENT_BOOTSTRAP.md",
    ROOT / "AUTHORITY_SECURITY_OVERLAY.json",
    ROOT / "NEW_PROJECT_BOOTSTRAP.json",
    ROOT / "REPOSITORY_BOOTSTRAP.md",
    BUS / "PROJECT_SCOPE_SELECTION_GATE_V1.md",
    BUS / "control/PROJECT_IDENTITY_LOCK.json",
    BUS / "control/PROJECT_MUTATION_AUTHORITY_V1.json",
    BUS / "control/PROJECT_MANIFEST.json",
    BUS / "control/MULTI_PROJECT_PROTOCOL_V3.md",
    BUS / "control/MESSAGE_ENVELOPE_SCHEMA.json",
    BUS / "control/DURABLE_COORDINATION_V1.md",
    BUS / "control/GITHUB_WRITE_SECURITY_POLICY.json",
    ROOT / "benefitflow_beta/coordination.py",
    ROOT / "benefitflow_beta/durable_store.py",
    ROOT / "benefitflow_beta/durable_coordination.py",
    ROOT / "benefitflow_beta/project_guard.py",
    ROOT / "tools/prove_multi_project_isolation.py",
    BUS / "discovery/AGENT_DISCOVERY.json",
    BUS / "control/PROJECT_SCOPE_BINDING.json",
    BUS / "control/GITHUB_REPOSITORY_BINDING.json",
    BUS / "control/RND_ROUND_GATE.json",
    BUS / "control/ACCEPTED_STATE.json",
    BUS / "control/P0_HARDENING_STATUS.json",
    BUS / "control/SWARM_ROSTER.json",
    BUS / "control/SWARM_PROTOCOL_V1.md",
    BUS / "control/FORUM_MESSAGE_ENVELOPE_V2.md",
    BUS / "control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
    BUS / "control/ENHANCEMENT_SOURCE_REGISTRY.json",
    BUS / "control/ENHANCEMENT_CURSOR.json",
    BUS / "control/SLACK_SCHEDULED_TASK_PROCESSING_V1.md",
    BUS / "control/AGENTBUS_MESSAGE_PERSISTENCE_CONTRACT_V1.md",
    BUS / "control/DEPLOYMENT_AGENTBUS_SNAPSHOT_CONTRACT_V1.md",
    BUS / "control/CONTROLLER_SUCCESSION_V1.md",
    BUS / "control/RECURSIVE_BACKUP_AND_RECOVERY_V1.md",
    BUS / "bootstrap/PRIMARY.md",
    BUS / "bootstrap/MANAGER.md",
    BUS / "bootstrap/RESEARCH.md",
    BUS / "bootstrap/REVIEWER.md",
    BUS / "bootstrap/SPECIALIST.md",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = BUS / 'backups' / ts / 'DEPLOYMENT_METADATA' / 'AGENTBUS_SNAPSHOT'
    out.mkdir(parents=True, exist_ok=False)
    files, failures = [], []
    messages = sorted((BUS / 'forum/messages').glob('*'))
    sources = [*messages, *REQUIRED]
    seen = set()
    for src in sources:
        key = str(src)
        if key in seen:
            continue
        seen.add(key)
        if not src.exists() or not src.is_file():
            failures.append(str(src.relative_to(ROOT)))
            continue
        rel = src.relative_to(ROOT)
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files.append({
            "source": str(rel),
            "packaged": str(dst.relative_to(out)),
            "bytes": dst.stat().st_size,
            "sha256": sha256(dst),
        })

    roster_path = BUS / "control/SWARM_ROSTER.json"
    spawn_policy = "UNAVAILABLE"
    if roster_path.is_file():
        spawn_policy = json.loads(roster_path.read_text(encoding="utf-8")).get("claim_policy", "UNAVAILABLE")
    identity_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in IDENTITY_ARTIFACTS if path.is_file()}
    project_manifest = json.loads((BUS / "control/PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    manifest = {
        "schema": "benefitflow/agentbus-snapshot/v7",
        "project_id": "benefitflow",
        "project_version": project_manifest["project_version"],
        "protocol_version": project_manifest["protocol_version"],
        "package_version": project_manifest["package_version"],
        "repository_target": project_manifest["repository_identity"],
        "repository_id": project_manifest.get("repository_id"),
        "canonical_branch": "main",
        "coordination_namespace": "BenefitFlow-AgentBus/",
        "identity_mode": "FAIL_CLOSED",
        "export_utc": datetime.now(timezone.utc).isoformat(),
        "source_forum": "BenefitFlow-AgentBus/forum/messages/",
        "message_count": len(messages),
        "file_count": len(files),
        "agent_spawn_policy": spawn_policy,
        "identity_artifact_hashes": identity_hashes,
        "recursive_enhancement_included": True,
        "multi_project_protocol": "BenefitFlow-AgentBus/control/MULTI_PROJECT_PROTOCOL_V3.md",
        "message_schema": "BenefitFlow-AgentBus/control/MESSAGE_ENVELOPE_SCHEMA.json",
        "durable_coordination": "BenefitFlow-AgentBus/control/DURABLE_COORDINATION_V1.md",
        "coordination_backend": project_manifest.get("coordination_backend"),
        "append_only_audit_included": True,
        "append_only_outbox_included": True,
        "multi_project_proving_harness_included": True,
        "github_write_security_policy_included": True,
        "project_mutation_authority_included": True,
        "authority_security_overlay_included": True,
        "communication_awareness_bootstrap_included": True,
        "new_project_factory_pointer_included": True,
        "foreign_source_mode": "READ_ONLY_FOREIGN_SOURCES",
        "required_control_files": [str(p.relative_to(ROOT)) for p in REQUIRED],
        "files": files,
        "failures": failures,
        "AGENTBUS_SNAPSHOT_COMPLETE": not failures and len(identity_hashes) == len(IDENTITY_ARTIFACTS) and len([x for x in files if x['source'].startswith('BenefitFlow-AgentBus/forum/messages/')]) == len(messages),
    }
    (out / 'SNAPSHOT_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + "\n", encoding='utf-8')
    print(out.parents[1])
    if not manifest['AGENTBUS_SNAPSHOT_COMPLETE']:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
