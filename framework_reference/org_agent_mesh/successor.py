from pathlib import Path
import json, shutil
from .constants import FRAMEWORK_VERSION
from .integrity import build_sha256sums

def create_successor_package(project_root, output_dir):
    src=Path(project_root); out=Path(output_dir)
    framework_root=Path(__file__).resolve().parents[1]
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    required=[
        "PROJECT_MANIFEST.json","PROJECT_CHARTER.md","ASSUMPTIONS_LOG.json","OPEN_QUESTIONS.json",
        "SOURCE_OF_TRUTH_MAP.json","INITIAL_WORK_BREAKDOWN.json","INITIAL_AGENT_REGISTRY.json",
        "INITIAL_REVIEW_PLAN.json","INITIAL_VALIDATION_PLAN.json","INITIAL_DECISION_LOG.json",
        "PROJECT_PACKAGE_MANIFEST.json","ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json"
    ]
    missing=[]
    for rel in required:
        p=src/rel
        if not p.exists(): missing.append(rel); continue
        dest=out/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
    if missing: raise FileNotFoundError(f"Cannot create successor; missing {missing}")
    # Copy only the minimum framework contracts needed to reconstruct behavior.
    for dirname in ["protocols","bootstrap"]:
        shutil.copytree(framework_root/dirname,out/"framework"/dirname)
    for fname in ["message.schema.json","agent_discovery.schema.json","project_manifest.schema.json","artifact_manifest.schema.json","presence_frame.schema.json","lane_claim.schema.json"]:
        dest=out/"framework"/"schemas"/fname; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(framework_root/"schemas"/fname,dest)
    operational={}
    for name in ["active_lanes","unresolved_blockers","accepted_state","latest_reviewed_lessons"]:
        p=src/"ORG_AGENT_MESH"/"control"/f"{name}.json"
        operational[name]=json.loads(p.read_text()) if p.exists() else []
    manifest={"schema":"org-agent-mesh/successor-package/v1","framework_version":FRAMEWORK_VERSION,
              "project_id":json.loads((src/"PROJECT_MANIFEST.json").read_text())["project_id"],
              "included_files":required,"operational_state":operational,
              "required_communication_schema":"framework/schemas/message.schema.json",
              "required_bootstrap_root":"framework/bootstrap",
              "required_protocol_root":"framework/protocols",
              "history_policy":"CANONICAL_POINTERS_PLUS_GOVERNED_AUDIT_ARCHIVE"}
    (out/"SUCCESSOR_MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (out/"SHA256SUMS.txt").write_text(build_sha256sums(out),encoding="utf-8")
    return out
