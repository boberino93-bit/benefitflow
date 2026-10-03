#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benefitflow_coordination.constants import (
    DEPLOYMENT_ROLES, FRAMEWORK_VERSION, PACKAGE_VERSION, PROJECT_ID, PROJECT_VERSION,
    PROTOCOL_VERSION, REPOSITORY_IDENTITY, ROLE_CAPABILITIES,
)
from benefitflow_coordination.packages import validate_agent_package_manifest

ROLES = ("PRIMARY", "MANAGER", "RESEARCH")
SHARED_EXPLICIT = [
    "PROJECT_MANIFEST.json",
    "ARCHITECTURE.md",
    "PROTOCOL_HARDENING_V2.md",
    "UPSTREAM_INTERCOMMUNICATIONS_BASELINE.md",
    "REPOSITORY_BOOTSTRAP.md",
    "BenefitFlow-AgentBus/PROJECT_SCOPE_SELECTION_GATE_V2.md",
    "BenefitFlow-AgentBus/discovery/AGENT_DISCOVERY.json",
    "BenefitFlow-AgentBus/control/PROJECT_SCOPE_BINDING.json",
    "BenefitFlow-AgentBus/control/GITHUB_REPOSITORY_BINDING.json",
    "BenefitFlow-AgentBus/control/PROTOCOL_STATE.json",
    "BenefitFlow-AgentBus/control/PROTOCOL_MIGRATION_V1_TO_V2.json",
    "BenefitFlow-AgentBus/control/AGENTBUS_MESSAGE_PROTOCOL_V2.md",
    "BenefitFlow-AgentBus/control/CAPABILITY_POLICY.json",
    "BenefitFlow-AgentBus/control/RND_ROUND_GATE.json",
    "BenefitFlow-AgentBus/control/PACKAGE_DEPENDENCY_MAP.json",
    "BenefitFlow-AgentBus/control/PACKAGE_REGISTRY.json",
]


def _sha(path: Path):
    return sha256(path.read_bytes()).hexdigest()


def collect_shared_files():
    files = [ROOT / item for item in SHARED_EXPLICIT]
    files += sorted((ROOT / "benefitflow_coordination").glob("*.py"))
    files += sorted((ROOT / "schemas").glob("*.json"))
    missing = [str(p.relative_to(ROOT)) for p in files if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing package inputs: {missing}")
    return files


def _build_timestamp(source_revision: str):
    try:
        result = subprocess.run(["git", "show", "-s", "--format=%cI", source_revision], cwd=ROOT, capture_output=True, text=True, check=True)
        value = result.stdout.strip()
        if value:
            return value
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_role(role: str, source_revision: str, dist: Path, built_at: str):
    if role not in ROLES:
        raise ValueError(role)
    if not source_revision or source_revision == "UNKNOWN":
        raise ValueError("source revision is required")
    role_bootstrap = ROOT / "BenefitFlow-AgentBus" / "bootstrap" / f"{role}.md"
    if not role_bootstrap.is_file():
        raise FileNotFoundError(role_bootstrap)

    with tempfile.TemporaryDirectory() as td:
        staging = Path(td)
        included = []
        component_hashes = {}
        for src in collect_shared_files():
            rel = src.relative_to(ROOT)
            dst = staging / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            included.append(rel.as_posix())
            component_hashes[rel.as_posix()] = _sha(src)

        bootstrap_dst = staging / "BOOTSTRAP.md"
        shutil.copy2(role_bootstrap, bootstrap_dst)
        included.append("BOOTSTRAP.md")
        component_hashes["BOOTSTRAP.md"] = _sha(role_bootstrap)

        manifest = {
            "schema": "benefitflow/agent-deployment-manifest/v2",
            "project_id": PROJECT_ID,
            "repository_identity": REPOSITORY_IDENTITY,
            "deployment_role": role,
            "authority_tier": DEPLOYMENT_ROLES[role]["authority_tier"],
            "project_version": PROJECT_VERSION,
            "framework_version": FRAMEWORK_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "package_version": PACKAGE_VERSION,
            "source_revision": source_revision,
            "built_at": built_at,
            "included_components": sorted(included),
            "component_hashes": dict(sorted(component_hashes.items())),
            "capabilities": ROLE_CAPABILITIES[role],
        }
        validate_agent_package_manifest(manifest, expected_source_revision=source_revision)
        (staging / "DEPLOYMENT_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        filename = f"benefitflow-{role.lower()}-agent-v{PACKAGE_VERSION}.zip"
        output = dist / filename
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(path.relative_to(staging).as_posix())
                    info.date_time = (2026, 1, 1, 0, 0, 0)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, path.read_bytes())
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--dist", default="dist")
    args = parser.parse_args()
    dist = ROOT / args.dist
    dist.mkdir(parents=True, exist_ok=True)
    for old in dist.glob("benefitflow-*-agent-v*.zip"):
        old.unlink()
    built_at = _build_timestamp(args.source_revision)
    packages = [build_role(role, args.source_revision, dist, built_at) for role in ROLES]
    release = {
        "schema": "benefitflow/agent-package-release-set/v1",
        "project_id": PROJECT_ID,
        "project_version": PROJECT_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "package_version": PACKAGE_VERSION,
        "source_revision": args.source_revision,
        "packages": {
            p.name: {"sha256": sha256(p.read_bytes()).hexdigest(), "size": p.stat().st_size}
            for p in packages
        },
    }
    (dist / "RELEASE_SET.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    print(json.dumps(release, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
