from __future__ import annotations
import json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / 'BenefitFlow-AgentBus'

ROLE_ALIASES = {
    'PRIMARY': 'PRIMARY',
    'MANAGER': 'MANAGER',
    'RESEARCH': 'RESEARCH',
    # Backward-compatible aliases from the pre-swarm role model.
    'REVIEWER': 'MANAGER',
    'SPECIALIST': 'RESEARCH',
}


def main():
    requested_role = (sys.argv[1] if len(sys.argv) > 1 else 'PRIMARY').upper()
    if requested_role not in ROLE_ALIASES:
        raise SystemExit('invalid role; expected PRIMARY, MANAGER, or RESEARCH')

    role = ROLE_ALIASES[requested_role]
    subprocess.run(
        [sys.executable, str(ROOT / 'tools/build_recursive_backup.py')],
        check=True,
        capture_output=True,
        text=True,
    )

    candidates = sorted(p for p in (BUS / 'backups').iterdir() if p.is_dir())
    latest = candidates[-1]
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    role_dir = BUS / 'artifactory' / role.lower()
    role_dir.mkdir(parents=True, exist_ok=True)
    out = role_dir / f'{ts}-successor-{role.lower()}'
    out.mkdir(parents=True, exist_ok=False)

    shutil.copytree(latest / 'DEPLOYMENT_METADATA', out / 'DEPLOYMENT_METADATA')
    shutil.copy2(BUS / 'bootstrap' / f'{role}.md', out / f'{role}_BOOTSTRAP.md')

    manifest = {
        'schema': 'benefitflow/successor-package/v2',
        'project_id': 'benefitflow',
        'requested_role': requested_role,
        'role': role,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'repository_target': 'boberino93-bit/benefitflow',
        'repository_binding_status': 'BOUND',
        'requires_revalidation': True,
        'authority_granted': False,
        'swarm_roster': 'BenefitFlow-AgentBus/control/SWARM_ROSTER.json',
        'swarm_protocol': 'BenefitFlow-AgentBus/control/SWARM_PROTOCOL_V1.md',
        'snapshot': str(
            (out / 'DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/SNAPSHOT_MANIFEST.json').relative_to(ROOT)
        ),
    }
    (out / 'SUCCESSOR_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
