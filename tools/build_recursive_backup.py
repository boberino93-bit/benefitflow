from __future__ import annotations
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"
REQUIRED = [
    BUS / "discovery/AGENT_DISCOVERY.json",
    BUS / "PROJECT_SCOPE_SELECTION_GATE_V1.md",
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
    # Legacy role aliases remain packaged for backward compatibility.
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
    files = []
    failures = []
    sources = []
    messages = sorted((BUS / 'forum/messages').glob('*'))
    sources.extend(messages)
    sources.extend(REQUIRED)

    for src in sources:
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

    manifest = {
        "schema": "benefitflow/agentbus-snapshot/v3",
        "project_id": "benefitflow",
        "export_utc": datetime.now(timezone.utc).isoformat(),
        "source_forum": "BenefitFlow-AgentBus/forum/messages/",
        "message_count": len(messages),
        "file_count": len(files),
        "recursive_enhancement_included": True,
        "foreign_source_mode": "READ_ONLY_FOREIGN_SOURCES",
        "required_control_files": [str(p.relative_to(ROOT)) for p in REQUIRED],
        "files": files,
        "failures": failures,
        "AGENTBUS_SNAPSHOT_COMPLETE": (
            not failures
            and len([
                x for x in files
                if x['source'].startswith('BenefitFlow-AgentBus/forum/messages/')
            ]) == len(messages)
        ),
    }
    (out / 'SNAPSHOT_MANIFEST.json').write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding='utf-8',
    )
    print(out.parents[1])
    if not manifest['AGENTBUS_SNAPSHOT_COMPLETE']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
