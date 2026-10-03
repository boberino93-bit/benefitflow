from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"

ROLES = ("PRIMARY", "MANAGER", "RESEARCH")
REQUIRED_CONTEXT = (
    BUS / "control" / "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
    BUS / "control" / "ENHANCEMENT_SOURCE_REGISTRY.json",
    BUS / "control" / "ENHANCEMENT_CURSOR.json",
)


def verify_source_parity() -> list[str]:
    errors: list[str] = []

    for path in REQUIRED_CONTEXT:
        if not path.is_file():
            errors.append(f"missing required enhancement context: {path.relative_to(ROOT)}")

    for role in ROLES:
        bootstrap = BUS / "bootstrap" / f"{role}.md"
        if not bootstrap.is_file():
            errors.append(f"missing role bootstrap: {bootstrap.relative_to(ROOT)}")
            continue
        text = bootstrap.read_text(encoding="utf-8")
        if "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md" not in text:
            errors.append(f"{role} bootstrap does not bind recursive enhancement protocol")
        if "read-only" not in text.lower():
            errors.append(f"{role} bootstrap does not state foreign read-only boundary")

    generator = ROOT / "tools" / "generate_successor_package.py"
    if not generator.is_file():
        errors.append("missing successor package generator")
    else:
        text = generator.read_text(encoding="utf-8")
        for token in (
            "ENHANCEMENT_CONTEXT",
            "READ_ONLY_FOREIGN_SOURCES",
            "foreign_mutation_allowed",
            "RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md",
        ):
            if token not in text:
                errors.append(f"successor package generator missing enhancement token: {token}")

    return errors


def verify_generated_package(package: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = package / "SUCCESSOR_MANIFEST.json"
    if not manifest_path.is_file():
        return [f"missing successor manifest: {manifest_path}"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("foreign_source_mode") != "READ_ONLY_FOREIGN_SOURCES":
        errors.append("package foreign_source_mode is not READ_ONLY_FOREIGN_SOURCES")
    if manifest.get("foreign_mutation_allowed") is not False:
        errors.append("package does not explicitly disable foreign mutation")

    context = package / "ENHANCEMENT_CONTEXT"
    for source in REQUIRED_CONTEXT:
        packaged = context / source.name
        if not packaged.is_file():
            errors.append(f"package missing enhancement context: {packaged.name}")

    role = manifest.get("role")
    if role not in ROLES:
        errors.append(f"unexpected package role: {role!r}")
    elif not (package / f"{role}_BOOTSTRAP.md").is_file():
        errors.append(f"package missing {role}_BOOTSTRAP.md")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BenefitFlow recursive-enhancement role-package parity.")
    parser.add_argument("--package", action="append", default=[], help="Optional generated successor package to validate.")
    args = parser.parse_args()

    errors = verify_source_parity()
    for package in args.package:
        errors.extend(verify_generated_package(Path(package)))

    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(2)

    print(json.dumps({"valid": True, "roles": list(ROLES)}, indent=2))


if __name__ == "__main__":
    main()
