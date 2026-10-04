from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"
ROLES = ("PRIMARY", "MANAGER", "RESEARCH")
EXPECTED_PROTOCOL_VERSION = "3.1.0"
EXPECTED_REPOSITORY_ID = 1403645790
EXPECTED_PACKAGE_SCHEMA = "benefitflow/successor-package/v7"

REQUIRED_IDENTITY = (
    ROOT / "AGENT_BOOTSTRAP.json",
    ROOT / "AGENT_BOOTSTRAP.md",
    ROOT / "REPOSITORY_BOOTSTRAP.md",
    BUS / "PROJECT_SCOPE_SELECTION_GATE_V1.md",
    BUS / "control" / "PROJECT_IDENTITY_LOCK.json",
    BUS / "control" / "PROJECT_SCOPE_BINDING.json",
    BUS / "control" / "GITHUB_REPOSITORY_BINDING.json",
    BUS / "discovery" / "AGENT_DISCOVERY.json",
)
REQUIRED_PROTOCOL = (
    BUS / "control" / "PROJECT_MANIFEST.json",
    BUS / "control" / "MULTI_PROJECT_PROTOCOL_V3.md",
    BUS / "control" / "MESSAGE_ENVELOPE_SCHEMA.json",
    ROOT / "benefitflow_beta" / "coordination.py",
    ROOT / "benefitflow_beta" / "project_guard.py",
)
REQUIRED_CONTEXT = (
    BUS / "control" / "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
    BUS / "control" / "ENHANCEMENT_SOURCE_REGISTRY.json",
    BUS / "control" / "ENHANCEMENT_CURSOR.json",
    ROOT / "SWARM_LAUNCH_KERNEL_V1.md",
    ROOT / "swarm_kernel" / "project.json",
    ROOT / "swarm_kernel" / "AGENT_BOOTSTRAP_OVERLAY.md",
    ROOT / "swarm_kernel" / "kernel.py",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_revision() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def verify_source_parity() -> list[str]:
    errors: list[str] = []
    for path in (*REQUIRED_IDENTITY, *REQUIRED_PROTOCOL, *REQUIRED_CONTEXT):
        if not path.is_file():
            errors.append(f"missing required package context: {path.relative_to(ROOT)}")

    lock_path = BUS / "control/PROJECT_IDENTITY_LOCK.json"
    if lock_path.is_file():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        expected = {"project_id": "benefitflow", "writable_repository": "boberino93-bit/benefitflow", "canonical_branch": "main", "coordination_root": "BenefitFlow-AgentBus/", "mode": "FAIL_CLOSED", "cross_project_write_policy": "DENY"}
        for key, value in expected.items():
            if lock.get(key) != value:
                errors.append(f"identity lock mismatch for {key}: {lock.get(key)!r}")

    binding_path = BUS / "control/GITHUB_REPOSITORY_BINDING.json"
    if binding_path.is_file():
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        expected_binding = {"target_repository": "boberino93-bit/benefitflow", "target_repository_id": EXPECTED_REPOSITORY_ID, "canonical_branch": "main", "foreign_write_policy": "DENY", "cross_project_bridge_policy": "EXPLICIT_COPY_BY_VALUE_ONLY"}
        for key, value in expected_binding.items():
            if binding.get(key) != value:
                errors.append(f"GitHub binding mismatch for {key}: {binding.get(key)!r}")

    root_bootstrap = ROOT / "AGENT_BOOTSTRAP.json"
    if root_bootstrap.is_file():
        root_contract = json.loads(root_bootstrap.read_text(encoding="utf-8"))
        if root_contract.get("project_id") != "benefitflow":
            errors.append("root bootstrap project mismatch")
        repo = root_contract.get("repository", {})
        if repo.get("full_name") != "boberino93-bit/benefitflow" or repo.get("id") != EXPECTED_REPOSITORY_ID:
            errors.append("root bootstrap repository mismatch")
        awareness = root_contract.get("communication_awareness", {})
        if awareness.get("default_visibility_claim") != "PARTIAL_UNLESS_PROVEN":
            errors.append("root bootstrap communication-awareness contract missing/stale")
        if root_contract.get("rules", {}).get("cross_project_write_default") != "DENY":
            errors.append("root bootstrap cross-project default is not DENY")

    kernel_cfg = ROOT / "swarm_kernel/project.json"
    if kernel_cfg.is_file():
        kernel = json.loads(kernel_cfg.read_text(encoding="utf-8"))
        expected_kernel = {"kernel_version": "1.0.0", "project_id": "benefitflow", "repository": "boberino93-bit/benefitflow", "canonical_branch": "main", "coordination_root": "BenefitFlow-AgentBus/", "state_root": ".swarm", "cross_project_telemetry": "READ_ONLY"}
        for key, value in expected_kernel.items():
            if kernel.get(key) != value:
                errors.append(f"swarm kernel mismatch for {key}: {kernel.get(key)!r}")

    project_path = BUS / "control/PROJECT_MANIFEST.json"
    if project_path.is_file():
        project = json.loads(project_path.read_text(encoding="utf-8"))
        expected = {"project_id": "benefitflow", "repository_identity": "boberino93-bit/benefitflow", "repository_id": EXPECTED_REPOSITORY_ID, "protocol_version": EXPECTED_PROTOCOL_VERSION, "cross_project_default": "DENY", "cross_project_bridge": "EXPLICIT_COPY_BY_VALUE_ONLY", "identity_mode": "FAIL_CLOSED", "message_schema": "BenefitFlow-AgentBus/control/MESSAGE_ENVELOPE_SCHEMA.json"}
        for key, value in expected.items():
            if project.get(key) != value:
                errors.append(f"project manifest mismatch for {key}: {project.get(key)!r}")
        for key in ("project_version", "package_version", "agent_namespace", "artifact_namespace", "message_namespace", "task_namespace", "lock_namespace"):
            if not project.get(key):
                errors.append(f"project manifest missing {key}")

    schema_path = BUS / "control/MESSAGE_ENVELOPE_SCHEMA.json"
    if schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if schema.get("$id") != "benefitflow/message-envelope/3.1.0":
            errors.append("message schema id/version mismatch")
        required = set(schema.get("required", []))
        for field in ("sender", "destination", "task", "artifact_refs", "integrity"):
            if field not in required:
                errors.append(f"message schema missing required field: {field}")
        task_required = set(schema.get("properties", {}).get("task", {}).get("required", []))
        if not {"project_id", "task_id"}.issubset(task_required):
            errors.append("message schema does not require task project ownership")
        artifact_item_required = set(schema.get("properties", {}).get("artifact_refs", {}).get("items", {}).get("required", []))
        if not {"project_id", "artifact_id"}.issubset(artifact_item_required):
            errors.append("message schema does not require artifact project ownership")

    discovery_path = BUS / "discovery/AGENT_DISCOVERY.json"
    if discovery_path.is_file():
        discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        if discovery.get("bootstrap_order", [])[:2] != ["../PROJECT_SCOPE_SELECTION_GATE_V1.md", "../control/PROJECT_IDENTITY_LOCK.json"]:
            errors.append("discovery bootstrap does not start with scope gate + identity lock")

    for role in ROLES:
        bootstrap = BUS / "bootstrap" / f"{role}.md"
        if not bootstrap.is_file():
            errors.append(f"missing role bootstrap: {bootstrap.relative_to(ROOT)}")
            continue
        text = bootstrap.read_text(encoding="utf-8")
        for token in ("RECENT CONTEXT IS NOT PROJECT AUTHORITY", "PROJECT_IDENTITY_LOCK.json", "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md", "3.1.0", "MESSAGE_ENVELOPE_SCHEMA.json"):
            if token not in text:
                errors.append(f"{role} bootstrap missing required token: {token}")
        if "read-only" not in text.lower():
            errors.append(f"{role} bootstrap does not state foreign read-only boundary")

    generator = ROOT / "tools/generate_successor_package.py"
    if not generator.is_file():
        errors.append("missing successor package generator")
    else:
        text = generator.read_text(encoding="utf-8")
        for token in ("IDENTITY_CONTEXT", "PROTOCOL_CONTEXT", "AGENT_BOOTSTRAP.json", "MESSAGE_ENVELOPE_SCHEMA.json", "project_guard.py", "agent_lifecycle_binding_required", "child_project_inheritance_required", "task_artifact_project_ownership_required", "EXPLICIT_COPY_BY_VALUE_ONLY", "source_revision", "READ_ONLY_FOREIGN_SOURCES", "foreign_mutation_allowed", "verify_role_package_enhancement_sync.py"):
            if token not in text:
                errors.append(f"successor package generator missing required token: {token}")
    return errors


def verify_hash_context(package: Path, context_dir: str, hashes: dict[str, str], sources: tuple[Path, ...], errors: list[str]) -> None:
    context = package / context_dir
    if not context.is_dir():
        errors.append(f"package missing {context_dir}")
        return
    for source in sources:
        packaged = context / source.name
        if not packaged.is_file():
            errors.append(f"package missing {context_dir} artifact: {source.name}")
            continue
        rel = str(packaged.relative_to(package))
        if hashes.get(rel) != sha256(packaged):
            errors.append(f"manifest checksum mismatch: {rel}")
        if sha256(packaged) != sha256(source):
            errors.append(f"package drift detected against source: {source.relative_to(ROOT)}")


def verify_generated_package(package: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = package / "SUCCESSOR_MANIFEST.json"
    if not manifest_path.is_file():
        return [f"missing successor manifest: {manifest_path}"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project = json.loads((BUS / "control/PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    expected_manifest = {"schema": EXPECTED_PACKAGE_SCHEMA, "project_id": "benefitflow", "repository_target": "boberino93-bit/benefitflow", "repository_id": EXPECTED_REPOSITORY_ID, "canonical_branch": "main", "coordination_namespace": "BenefitFlow-AgentBus/", "artifact_namespace": "BenefitFlow-AgentBus/artifactory/", "identity_mode": "FAIL_CLOSED", "foreign_source_mode": "READ_ONLY_FOREIGN_SOURCES", "foreign_mutation_allowed": False, "cross_project_default": "DENY", "cross_project_bridge": "EXPLICIT_COPY_BY_VALUE_ONLY", "agent_lifecycle_binding_required": True, "child_project_inheritance_required": True, "task_artifact_project_ownership_required": True, "message_schema": "PROTOCOL_CONTEXT/MESSAGE_ENVELOPE_SCHEMA.json", "project_version": project["project_version"], "protocol_version": project["protocol_version"], "package_version": project["package_version"], "swarm_kernel_version": "1.0.0", "swarm_kernel_required": True}
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            errors.append(f"package manifest mismatch for {key}: {manifest.get(key)!r}")

    revision = manifest.get("source_revision")
    live_revision = current_revision()
    if not revision or revision == "UNAVAILABLE":
        errors.append("package source_revision is unavailable")
    elif live_revision != "UNAVAILABLE" and revision != live_revision:
        errors.append(f"package source revision {revision} does not match live revision {live_revision}")

    role = manifest.get("role")
    if role not in ROLES:
        errors.append(f"unexpected package role: {role!r}")
    else:
        role_bootstrap = package / f"{role}_BOOTSTRAP.md"
        if not role_bootstrap.is_file():
            errors.append(f"package missing {role}_BOOTSTRAP.md")
        elif manifest.get("bootstrap_sha256") != sha256(role_bootstrap):
            errors.append(f"packaged {role} bootstrap checksum mismatch")

    verify_hash_context(package, "IDENTITY_CONTEXT", manifest.get("identity_artifact_hashes", {}), REQUIRED_IDENTITY, errors)
    verify_hash_context(package, "PROTOCOL_CONTEXT", manifest.get("protocol_artifact_hashes", {}), REQUIRED_PROTOCOL, errors)

    snapshot_root = package / "DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT"
    for source in (*REQUIRED_IDENTITY, *REQUIRED_PROTOCOL):
        packaged = snapshot_root / source.relative_to(ROOT)
        if not packaged.is_file():
            errors.append(f"snapshot missing required artifact: {source.relative_to(ROOT)}")

    context = package / "ENHANCEMENT_CONTEXT"
    for source in REQUIRED_CONTEXT:
        packaged = context / source.name
        if not packaged.is_file():
            errors.append(f"package missing enhancement/kernel context: {packaged.name}")
        elif sha256(packaged) != sha256(source):
            errors.append(f"package enhancement/kernel drift: {source.relative_to(ROOT)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BenefitFlow identity, protocol 3.1, lifecycle, ownership, enhancement, kernel, recovery, and package parity.")
    parser.add_argument("--package", action="append", default=[])
    args = parser.parse_args()
    errors = verify_source_parity()
    for package in args.package:
        errors.extend(verify_generated_package(Path(package)))
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(2)
    print(json.dumps({"valid": True, "roles": list(ROLES), "identity_mode": "FAIL_CLOSED", "protocol_version": EXPECTED_PROTOCOL_VERSION, "repository_id": EXPECTED_REPOSITORY_ID, "package_schema": EXPECTED_PACKAGE_SCHEMA, "swarm_kernel_version": "1.0.0"}, indent=2))


if __name__ == "__main__":
    main()
