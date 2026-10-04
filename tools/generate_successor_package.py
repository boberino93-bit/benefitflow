from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / 'BenefitFlow-AgentBus'

ROLE_ALIASES = {
    'PRIMARY': 'PRIMARY',
    'MANAGER': 'MANAGER',
    'RESEARCH': 'RESEARCH',
    'REVIEWER': 'MANAGER',
    'SPECIALIST': 'RESEARCH',
}

IDENTITY_CONTEXT = [
    BUS / 'PROJECT_SCOPE_SELECTION_GATE_V1.md',
    BUS / 'control' / 'PROJECT_IDENTITY_LOCK.json',
    BUS / 'control' / 'PROJECT_SCOPE_BINDING.json',
    BUS / 'control' / 'GITHUB_REPOSITORY_BINDING.json',
    BUS / 'discovery' / 'AGENT_DISCOVERY.json',
]

PROTOCOL_CONTEXT = [
    BUS / 'control' / 'PROJECT_MANIFEST.json',
    BUS / 'control' / 'MULTI_PROJECT_PROTOCOL_V3.md',
    ROOT / 'benefitflow_beta' / 'coordination.py',
]

ENHANCEMENT_CONTEXT = [
    BUS / 'control' / 'RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md',
    BUS / 'control' / 'ENHANCEMENT_SOURCE_REGISTRY.json',
    BUS / 'control' / 'ENHANCEMENT_CURSOR.json',
    ROOT / 'SWARM_LAUNCH_KERNEL_V1.md',
    ROOT / 'swarm_kernel' / 'project.json',
    ROOT / 'swarm_kernel' / 'AGENT_BOOTSTRAP_OVERLAY.md',
    ROOT / 'swarm_kernel' / 'kernel.py',
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def source_revision() -> str:
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return 'UNAVAILABLE'


def main():
    requested_role = (sys.argv[1] if len(sys.argv) > 1 else 'PRIMARY').upper()
    if requested_role not in ROLE_ALIASES:
        raise SystemExit('invalid role; expected PRIMARY, MANAGER, or RESEARCH')
    role = ROLE_ALIASES[requested_role]
    revision = source_revision()
    if revision == 'UNAVAILABLE':
        raise SystemExit('cannot create continuation package without exact git source revision')

    for dependency in (*IDENTITY_CONTEXT, *PROTOCOL_CONTEXT, *ENHANCEMENT_CONTEXT):
        if not dependency.is_file():
            raise SystemExit(f'missing package dependency: {dependency.relative_to(ROOT)}')

    lock = json.loads((BUS / 'control/PROJECT_IDENTITY_LOCK.json').read_text(encoding='utf-8'))
    project = json.loads((BUS / 'control/PROJECT_MANIFEST.json').read_text(encoding='utf-8'))
    expected_identity = {
        'project_id': 'benefitflow',
        'writable_repository': 'boberino93-bit/benefitflow',
        'canonical_branch': 'main',
        'coordination_root': 'BenefitFlow-AgentBus/',
        'mode': 'FAIL_CLOSED',
    }
    for key, expected in expected_identity.items():
        if lock.get(key) != expected:
            raise SystemExit(f'identity lock mismatch for {key}: {lock.get(key)!r} != {expected!r}')
    if project.get('project_id') != 'benefitflow' or project.get('repository_identity') != 'boberino93-bit/benefitflow':
        raise SystemExit('canonical project manifest does not match BenefitFlow binding')

    subprocess.run([sys.executable, str(ROOT / 'tools/build_recursive_backup.py')], check=True, capture_output=True, text=True)
    candidates = sorted(p for p in (BUS / 'backups').iterdir() if p.is_dir())
    latest = candidates[-1]
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')

    role_dir = BUS / 'artifactory' / role.lower()
    role_dir.mkdir(parents=True, exist_ok=True)
    out = role_dir / f'{ts}-successor-{role.lower()}'
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(latest / 'DEPLOYMENT_METADATA', out / 'DEPLOYMENT_METADATA')
    shutil.copy2(BUS / 'bootstrap' / f'{role}.md', out / f'{role}_BOOTSTRAP.md')

    identity_out = out / 'IDENTITY_CONTEXT'
    identity_out.mkdir(parents=True, exist_ok=False)
    identity_hashes = {}
    for src in IDENTITY_CONTEXT:
        dst = identity_out / src.name
        shutil.copy2(src, dst)
        identity_hashes[str(dst.relative_to(out))] = sha256(dst)

    protocol_out = out / 'PROTOCOL_CONTEXT'
    protocol_out.mkdir(parents=True, exist_ok=False)
    protocol_hashes = {}
    for src in PROTOCOL_CONTEXT:
        dst = protocol_out / src.name
        shutil.copy2(src, dst)
        protocol_hashes[str(dst.relative_to(out))] = sha256(dst)

    enhancement_out = out / 'ENHANCEMENT_CONTEXT'
    enhancement_out.mkdir(parents=True, exist_ok=False)
    for src in ENHANCEMENT_CONTEXT:
        shutil.copy2(src, enhancement_out / src.name)

    roster = json.loads((BUS / 'control/SWARM_ROSTER.json').read_text(encoding='utf-8'))
    bootstrap = out / f'{role}_BOOTSTRAP.md'
    manifest = {
        'schema': 'benefitflow/successor-package/v6',
        'package_id': f"benefitflow:{role.lower()}:{project['package_version']}:{ts}",
        'project_id': project['project_id'],
        'project_name': project['project_name'],
        'project_version': project['project_version'],
        'protocol_version': project['protocol_version'],
        'package_version': project['package_version'],
        'package_type': 'successor-continuation',
        'requested_role': requested_role,
        'role': role,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_revision': revision,
        'repository_target': project['repository_identity'],
        'canonical_branch': 'main',
        'coordination_namespace': 'BenefitFlow-AgentBus/',
        'artifact_namespace': 'BenefitFlow-AgentBus/artifactory/',
        'identity_mode': 'FAIL_CLOSED',
        'repository_binding_status': 'BOUND',
        'requires_revalidation': True,
        'authority_granted': False,
        'agent_spawn_policy': roster.get('claim_policy'),
        'cross_project_default': 'DENY',
        'bootstrap_sha256': sha256(bootstrap),
        'identity_artifact_hashes': identity_hashes,
        'protocol_artifact_hashes': protocol_hashes,
        'foreign_source_mode': 'READ_ONLY_FOREIGN_SOURCES',
        'foreign_mutation_allowed': False,
        'swarm_kernel_version': '1.0.0',
        'swarm_kernel_required': True,
        'swarm_kernel_overlay': 'ENHANCEMENT_CONTEXT/AGENT_BOOTSTRAP_OVERLAY.md',
        'package_sync_required_after_control_plane_graft': True,
        'snapshot': 'DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/SNAPSHOT_MANIFEST.json',
    }
    (out / 'SUCCESSOR_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    subprocess.run(
        [sys.executable, str(ROOT / 'tools/verify_role_package_enhancement_sync.py'), '--package', str(out)],
        check=True, capture_output=True, text=True,
    )
    print(out)


if __name__ == '__main__':
    main()
