from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"
REGISTRY = BUS / "control" / "ENHANCEMENT_SOURCE_REGISTRY.json"
CURSOR = BUS / "control" / "ENHANCEMENT_CURSOR.json"

ALLOWED_COMPATIBILITY = {
    "SAFE_REUSABLE",
    "ADAPT_REQUIRED",
    "CONFLICT",
    "DUPLICATE",
    "OUT_OF_SCOPE",
    "SENSITIVE_OR_PROHIBITED",
}

REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id",
    "source_repository",
    "source_path",
    "source_ref",
    "concept_id",
    "compatibility",
    "observed_pattern",
    "expected_benefitflow_value",
    "affected_benefitflow_surfaces",
    "foreign_mutation_requested",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def candidate_fingerprint(source_repository: str, source_path: str, source_ref: str, concept_id: str) -> str:
    payload = "|".join([source_repository, source_path, source_ref, concept_id]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def next_source() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    cursor = load_json(CURSOR)
    sources = registry["sources"]
    if not sources:
        raise SystemExit("enhancement source registry is empty")
    index = int(cursor.get("next_source_index", 0)) % len(sources)
    return sources[index]


def validate_candidate(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - candidate.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    compatibility = candidate.get("compatibility")
    if compatibility not in ALLOWED_COMPATIBILITY:
        errors.append(f"invalid compatibility: {compatibility!r}")

    if candidate.get("foreign_mutation_requested") is not False:
        errors.append("foreign_mutation_requested must be false")

    if candidate.get("target_repository", "boberino93-bit/benefitflow") != "boberino93-bit/benefitflow":
        errors.append("target_repository must be boberino93-bit/benefitflow")

    source_repository = candidate.get("source_repository")
    if source_repository == "boberino93-bit/benefitflow":
        errors.append("source_repository must be foreign for a cross-project enhancement candidate")

    if all(k in candidate for k in ("source_repository", "source_path", "source_ref", "concept_id")):
        expected = candidate_fingerprint(
            candidate["source_repository"],
            candidate["source_path"],
            candidate["source_ref"],
            candidate["concept_id"],
        )
        supplied = candidate.get("fingerprint")
        if supplied is not None and supplied != expected:
            errors.append("candidate fingerprint does not match source identity")

    return errors


def record_scan(source_id: str, observed_head: str, result: str, candidate_ids: list[str]) -> None:
    registry = load_json(REGISTRY)
    cursor = load_json(CURSOR)
    sources = registry["sources"]
    source_ids = [source["source_id"] for source in sources]
    if source_id not in source_ids:
        raise SystemExit(f"unknown source_id: {source_id}")

    now = utc_now()
    state = cursor.setdefault("sources", {}).setdefault(source_id, {})
    source = sources[source_ids.index(source_id)]
    state.update(
        {
            "repository": source["repository"],
            "last_observed_head": observed_head,
            "last_scan_utc": now,
            "last_result": result,
            "candidate_ids": candidate_ids,
        }
    )
    cursor["cycles_completed"] = int(cursor.get("cycles_completed", 0)) + 1
    cursor["last_cycle_utc"] = now
    cursor["next_source_index"] = (source_ids.index(source_id) + 1) % len(sources)
    write_json(CURSOR, cursor)


def cmd_next_source(_: argparse.Namespace) -> None:
    print(json.dumps(next_source(), indent=2))


def cmd_fingerprint(args: argparse.Namespace) -> None:
    print(candidate_fingerprint(args.repository, args.path, args.ref, args.concept))


def cmd_validate(args: argparse.Namespace) -> None:
    candidate = load_json(Path(args.candidate))
    errors = validate_candidate(candidate)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(2)
    print(json.dumps({"valid": True}, indent=2))


def cmd_record_scan(args: argparse.Namespace) -> None:
    record_scan(args.source_id, args.head, args.result, args.candidate_id or [])
    print(json.dumps({"recorded": True, "source_id": args.source_id}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BenefitFlow-local helper for the read-only recursive enhancement cycle."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_next = sub.add_parser("next-source", help="Print the next foreign source selected by the local cursor.")
    p_next.set_defaults(func=cmd_next_source)

    p_fp = sub.add_parser("fingerprint", help="Create a stable enhancement candidate fingerprint.")
    p_fp.add_argument("repository")
    p_fp.add_argument("path")
    p_fp.add_argument("ref")
    p_fp.add_argument("concept")
    p_fp.set_defaults(func=cmd_fingerprint)

    p_validate = sub.add_parser("validate-candidate", help="Validate a local enhancement candidate JSON file.")
    p_validate.add_argument("candidate")
    p_validate.set_defaults(func=cmd_validate)

    p_record = sub.add_parser("record-scan", help="Advance the BenefitFlow-local source cursor after durable persistence.")
    p_record.add_argument("source_id")
    p_record.add_argument("head")
    p_record.add_argument("result")
    p_record.add_argument("--candidate-id", action="append", default=[])
    p_record.set_defaults(func=cmd_record_scan)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
