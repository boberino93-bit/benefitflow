from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"

ROLES = ("PRIMARY", "MANAGER", "RESEARCH")
REQUIRED_IDENTITY = (
    BUS / "PROJECT_SCOPE_SELECTION_GATE_V1.md",
    BUS / "control" / "PROJECT_IDENTITY_LOCK.json",
    BUS / "control" / "PROJECT_SCOPE_BINDING.json",
    BUS / "control" / "GITHUB_REPOSITORY_BINDING.json",
    BUS / "discovery" / "AGENT_DISCOVERY.json",
)
REQUIRED_CONTEXT = (
    BUS / "control" / "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
    BUS / "control" / "ENHANCEMENT_SOURCE_REGISTRY.json",
    BUS / "control" / "ENHANCEMENT_CURSOR.json",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def verify_source_parity() -> list[str]:
    errors: list[str] = []

    for path in (*REQUIRED_IDENTITY, *REQUIRED_CONTEXT):
        if not path.is_file():
            errors.append(f"missing required package context: {path.relative_to(ROOT)}")

    lock_path = BUS / "control/PROJECT_IDENTITY_LOCK.json"
    if lock_path.is_file():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        expected = {
            "project_id": "benefitflow",
            "writable_repository": "boberino93-bit/benefitflow",
            "canonical_branch": "main",
            "coordination_root": "BenefitFlow-AgentBus/",
            "mode": "FAIL_CLOSED",
            "cross_project_write_policy": "DENY",
        }
        for key, value in expected.items():
            if lock.get(key) != value:
                errors.append(f"identity lock mismatch for {key}: {lock.get(key)!r}")

    discovery_path = BUS / "discovery/AGENT_DISCOVERY.json"
    if discovery_path.is_file():
        discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        order = discovery.get("bootstrap_order", [])
        expected_first = [
            "../PROJECT_SCOPE_SELECTION_GATE_V1.md",
            "../control/PROJECT_IDENTITY_LOCK.json",
        ]
        if order[:2] != expected_first:
            errors.append(f"discovery bootstrap does not start with scope gate + identity lock: {order[:2]!r}")

    for role in ROLES:
        bootstrap = BUS / "bootstrap" / f"{role}.md"
        if not bootstrap.is_file():
            errors.append(f"missing role bootstrap: {bootstrap.relative_to(ROOT)}")
            continue
        text = bootstrap.read_text(encoding="utf-8")
        for token in (
            "RECENT CONTEXT IS NOT PROJECT AUTHORITY",
            "PROJECT_IDENTITY_LOCK.json",
            "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
        ):
            if token not in text:
                errors.append(f"{role} bootstrap missing required token: {token}")
        if "read-only" not in text.lower():
            errors.append(f"{role} bootstrap does not state foreign read-only boundary")

    generator = ROOT / "tools" / "generate_successor_package.py"
    if not generator.is_file():
        errors.append("missing successor package generator")
    else:
        text = generator.read_text(encoding="utf-8")
        for token in (
            "IDENTITY_CONTEXT",
            "identity_artifact_hashes",
            "source_revision",
            "agent_spawn_policy",
            "READ_ONLY_FOREIGN_SOURCES",
            "foreign_mutation_allowed",
            "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
            "verify_role_package_enhancement_sync.py",
        ):
            if token not in text:
                errors.append(f"successor package generator missing required token: {token}")

    return errors


def verify_generated_package(package: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = package / "SUCCESSOR_MANIFEST.json"
    if not manifest_path.is_file():
        return [f"missing successor manifest: {manifest_path}"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest = {
        "project_id": "benefitflow",
        "repository_target": "boberino93-bit/benefitflow",
        "canonical_branch": "main",
        "coordination_namespace": "BenefitFlow-AgentBus/",
        "artifact_namespace": "BenefitFlow-AgentBus/artifactory/",
        "identity_mode": "FAIL_CLOSED",
        "foreign_source_mode": "READ_ONLY_FOREIGN_SOURCES",
        "foreign_mutation_allowed": False,
    }
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            errors.append(f"package manifest mismatch for {key}: {manifest.get(key)!r}")

    revision = manifest.get("source_revision")
    if not revision or revision == "UNAVAILABLE":
        errors.append("package source_revision is unavailable")
    live_revision = current_revision()
    if live_revision != "UNAVAILABLE" and revision != live_revision:
        errors.append(f"package source revision {revision} does not match live revision {live_revision}")

    if not manifest.get("agent_spawn_policy"):
        errors.append("package does not declare current agent_spawn_policy")

    role = manifest.get("role")
    if role not in ROLES:
        errors.append(f"unexpected package role: {role!r}")
    else:
        role_bootstrap = package / f"{role}_BOOTSTRAP.md"
        if not role_bootstrap.is_file():
            errors.append(f"package missing {role}_BOOTSTRAP.md")
        else:
            text = role_bootstrap.read_text(encoding="utf-8")
            if "PROJECT_IDENTITY_LOCK.json" not in text or "RECENT CONTEXT IS NOT PROJECT AUTHORITY" not in text:
                errors.append(f"packaged {role} bootstrap lacks identity-first recovery rule")

    identity_context = package / "IDENTITY_CONTEXT"
    identity_hashes = manifest.get("identity_artifact_hashes", {})
    required_identity_names = {path.name for path in REQUIRED_IDENTITY}
    packaged_identity_names = {p.name for p in identity_context.iterdir()} if identity_context.is_dir() else set()
    if not required_identity_names.issubset(packaged_identity_names):
        errors.append("package identity context is incomplete")

    for rel, expected_hash in identity_hashes.items():
        packaged = package / rel
        if not packaged.is_file():
            errors.append(f"package missing identity artifact declared in manifest: {rel}")
        elif sha256(packaged) != expected_hash:
            errors.append(f"identity checksum mismatch: {rel}")

    packaged_lock = identity_context / "PROJECT_IDENTITY_LOCK.json"
    if packaged_lock.is_file():
        lock = json.loads(packaged_lock.read_text(encoding="utf-8"))
        if lock.get("mode") != "FAIL_CLOSED" or lock.get("project_id") != "benefitflow":
            errors.append("packaged project identity lock is invalid")

    snapshot_root = package / "DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT"
    for source in REQUIRED_IDENTITY:
        packaged = snapshot_root / source.relative_to(ROOT)
        if not packaged.is_file():
            errors.append(f"snapshot missing identity artifact: {source.relative_to(ROOT)}")

    context = package / "ENHANCEMENT_CONTEXT"
    for source in REQUIRED_CONTEXT:
        packaged = context / source.name
        if not packaged.is_file():
            errors.append(f"package missing enhancement context: {packaged.name}")

    expected_bootstrap_prefix = [
        "PROJECT_SCOPE_SELECTION_GATE_V1.md",
        "PROJECT_IDENTITY_LOCK.json",
        "PROJECT_SCOPE_BINDING.json",
        "GITHUB_REPOSITORY_BINDING.json",
    ]
    declared = manifest.get("bootstrap_order_required", [])
    if declared[:4] != expected_bootstrap_prefix:
        errors.append(f"package bootstrap order is not identity-first: {declared!r}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BenefitFlow identity, recovery, and recursive-enhancement role-package parity.")
    parser.add_argument("--package", action="append", default=[], help="Optional generated successor package to validate.")
    args = parser.parse_args()

    errors = verify_source_parity()
    for package in args.package:
        errors.extend(verify_generated_package(Path(package)))

    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(2)

    print(json.dumps({"valid": True, "roles": list(ROLES), "identity_mode": "FAIL_CLOSED"}, indent=2))


if __name__ == "__main__":
    main()
