#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benefitflow_coordination.constants import PACKAGE_VERSION, ROLE_CAPABILITIES
from benefitflow_coordination.packages import validate_agent_package_manifest

ROLES = ("PRIMARY", "MANAGER", "RESEARCH")
FORBIDDEN_MARKERS = [
    "DuoOpen-AgentBus/", "boberino93-bit/duo-open",
]


def verify_zip(path: Path, role: str, source_revision: str):
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        required = {"DEPLOYMENT_MANIFEST.json", "BOOTSTRAP.md", "PROJECT_MANIFEST.json", "BenefitFlow-AgentBus/control/PROTOCOL_STATE.json"}
        missing = required - names
        if missing:
            raise AssertionError(f"{path.name} missing {sorted(missing)}")
        manifest = json.loads(zf.read("DEPLOYMENT_MANIFEST.json"))
        validate_agent_package_manifest(manifest, expected_source_revision=source_revision)
        if manifest["deployment_role"] != role:
            raise AssertionError("wrong deployment role")
        if manifest["capabilities"] != ROLE_CAPABILITIES[role]:
            raise AssertionError("role capability drift")
        declared = set(manifest["included_components"])
        actual_payload = names - {"DEPLOYMENT_MANIFEST.json"}
        if declared != actual_payload:
            raise AssertionError("manifest component list drift")
        for component, expected_hash in manifest["component_hashes"].items():
            actual = sha256(zf.read(component)).hexdigest()
            if actual != expected_hash:
                raise AssertionError(f"component hash mismatch: {component}")
        for name in names:
            for marker in FORBIDDEN_MARKERS:
                if marker in name:
                    raise AssertionError(f"foreign project path in package: {name}")
        combined_text = "\n".join(
            zf.read(name).decode("utf-8", errors="ignore") for name in names if name.endswith((".md", ".json", ".py"))
        )
        if "project_id=duo-open" in combined_text or '"project_id": "duo-open"' in combined_text:
            raise AssertionError("foreign project identity embedded in package")
    return {"filename": path.name, "sha256": sha256(path.read_bytes()).hexdigest(), "entries": len(names)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--dist", default="dist")
    args = parser.parse_args()
    dist = ROOT / args.dist
    results = []
    for role in ROLES:
        path = dist / f"benefitflow-{role.lower()}-agent-v{PACKAGE_VERSION}.zip"
        if not path.exists():
            raise SystemExit(f"missing package: {path}")
        results.append(verify_zip(path, role, args.source_revision))
    release = json.loads((dist / "RELEASE_SET.json").read_text())
    if release["source_revision"] != args.source_revision:
        raise AssertionError("release-set source revision mismatch")
    if set(release["packages"]) != {r["filename"] for r in results}:
        raise AssertionError("release-set package list mismatch")
    for result in results:
        if release["packages"][result["filename"]]["sha256"] != result["sha256"]:
            raise AssertionError("release-set package hash mismatch")
    print(json.dumps({"verified": True, "packages": results}, indent=2))


if __name__ == "__main__":
    main()
