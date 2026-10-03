from pathlib import Path
import json, re, uuid
from datetime import datetime, timezone
from .constants import FRAMEWORK_VERSION
from .authority import capabilities_for

def _slug(s):
    s=re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
    return s[:48] or "project"

def _write_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def _infer_type(idea):
    t=idea.lower()
    if any(w in t for w in ("investigate","research","study")): return "RESEARCH_PROJECT"
    if any(w in t for w in ("analyze","analyse","forecast","compare")): return "ANALYSIS_PROJECT"
    if any(w in t for w in ("process","workflow","cycle time","improve")): return "PROCESS_IMPROVEMENT_PROJECT"
    if any(w in t for w in ("document","policy","guide","manual")): return "DOCUMENT_PROJECT"
    if any(w in t for w in ("implement","roll out","deploy")): return "IMPLEMENTATION_PROJECT"
    if any(w in t for w in ("software","application","service","code")): return "SOFTWARE_PROJECT"
    return "CUSTOM_PROJECT"

def initialize_project(idea, output_root, project_name=None, organization_domain="UNKNOWN"):
    if not idea or not idea.strip(): raise ValueError("idea must be non-empty")
    project_name=project_name or "Project from sparse intake"
    slug=_slug(project_name)
    project_id=f"prj-{uuid.uuid4().hex[:10]}"
    root=Path(output_root)/slug
    root.mkdir(parents=True,exist_ok=False)
    ptype=_infer_type(idea)
    manifest={
      "schema":"org-agent-mesh/project-manifest/v1","framework_version":FRAMEWORK_VERSION,
      "project_id":project_id,"project_name":project_name,"project_slug":slug,
      "problem_statement":idea.strip(),"desired_outcome":"UNKNOWN","deliverable_types":[],
      "project_type":ptype,"organization_domain":organization_domain,"stakeholders":[],"constraints":[],
      "non_goals":[],"assumptions":["Project type inferred from sparse intake and requires validation."],
      "authoritative_sources":[],"source_systems":[],"validation_methods":[],"approval_gates":[],
      "security_classification":"UNKNOWN","data_handling_rules":[],"allowed_tools":[],"prohibited_actions":[],
      "integration_authority":"ORCHESTRATOR","review_authority":"REVIEWER",
      "agent_roles":[
        {"role_id":"orchestrator-1","authority_tier":"ORCHESTRATOR","profile":"Integrator","capabilities":capabilities_for("ORCHESTRATOR")},
        {"role_id":"reviewer-1","authority_tier":"REVIEWER","profile":"Gatekeeper","capabilities":capabilities_for("REVIEWER")},
        {"role_id":"specialist-1","authority_tier":"SPECIALIST","profile":"General specialist","capabilities":capabilities_for("SPECIALIST")},
      ],
      "parallelism_limits":{"max_active_specialists":3,"status":"ASSUMED"},
      "human_required_actions":["Confirm desired outcome, stakeholders, authoritative sources, security classification, and approval gates."],
      "external_dependencies":[],"success_criteria":[],"completion_definition":"REQUIRES_HUMAN",
      "artifact_policy":{"immutability":True,"canonical_detail_home":"artifact","checksums":True},
      "communication_policy":{"append_only":True,"supersession_not_deletion":True,"messages_point_to_evidence":True},
      "learning_policy":{"review_required":True,"may_not_expand_authority":True}
    }
    _write_json(root/"PROJECT_MANIFEST.json",manifest)
    (root/"PROJECT_CHARTER.md").write_text(f"# Project Charter\n\n## Problem statement\n{idea.strip()}\n\n## Desired outcome\nUNKNOWN\n\n## Operating rule\nBegin bounded discovery work while keeping unknowns explicit. Accepted-state changes require configured authority.\n",encoding="utf-8")
    _write_json(root/"ASSUMPTIONS_LOG.json",[{"id":"asm-001","statement":"Project type was inferred from sparse intake.","status":"ASSUMED","value":ptype,"needs_validation":True}])
    _write_json(root/"OPEN_QUESTIONS.json",[
      {"id":"q-001","question":"What measurable outcome defines success?","status":"REQUIRES_HUMAN"},
      {"id":"q-002","question":"Which sources are authoritative for this work?","status":"REQUIRES_HUMAN"},
      {"id":"q-003","question":"What data/security classification applies?","status":"REQUIRES_HUMAN"},
      {"id":"q-004","question":"Which irreversible or external actions require approval?","status":"REQUIRES_HUMAN"}
    ])
    _write_json(root/"SOURCE_OF_TRUTH_MAP.json",{"status":"REQUIRES_HUMAN","sources":[]})
    _write_json(root/"INITIAL_RISK_REGISTER.json",[
      {"risk_id":"risk-001","risk":"Sparse intake may hide constraints.","status":"OPEN","mitigation":"Keep inferred facts as assumptions and validate before material accepted-state changes."},
      {"risk_id":"risk-002","risk":"Authority or data handling may be underspecified.","status":"OPEN","mitigation":"Use least privilege and require explicit configuration before external/irreversible actions."}
    ])
    _write_json(root/"INITIAL_WORK_BREAKDOWN.json",[
      {"lane_id":"lane-discovery","assignment":"Clarify outcome, authorities, constraints, and evidence sources.","scope":"Project intake and source-of-truth discovery","starting_project_state":"intake-v1","expected_output":"Validated discovery artifact","dependencies":[],"possible_overlap":[],"current_status":"OPEN"},
      {"lane_id":"lane-plan","assignment":"Draft implementation or investigation plan from validated discovery.","scope":"Work decomposition","starting_project_state":"intake-v1","expected_output":"Reviewed work plan","dependencies":["lane-discovery"],"possible_overlap":[],"current_status":"BLOCKED"}
    ])
    _write_json(root/"INITIAL_AGENT_REGISTRY.json",manifest["agent_roles"])
    _write_json(root/"INITIAL_REVIEW_PLAN.json",{"pipeline":["SPECIALIST","REVIEWER","ORCHESTRATOR"],"ready_for_integration_is_final_acceptance":False,"contradictions":"EVIDENCE_RECONCILIATION_NOT_VOTING"})
    _write_json(root/"INITIAL_VALIDATION_PLAN.json",{"status":"REQUIRES_HUMAN","methods":[],"rule":"Validation must match deliverable type and authoritative source."})
    _write_json(root/"INITIAL_DECISION_LOG.json",[])
    _write_json(root/"PROJECT_PACKAGE_MANIFEST.json",{
      "schema":"org-agent-mesh/project-package-manifest/v1","project_id":project_id,"framework_version":FRAMEWORK_VERSION,
      "package_state":"INITIALIZED","required_files":["PROJECT_MANIFEST.json","ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json","SOURCE_OF_TRUTH_MAP.json"],
      "integrity_status":"PENDING_INITIAL_HASH","sanitization_status":"PROJECT_INSTANCE_POLICY_APPLIES"
    })
    mesh=root/"ORG_AGENT_MESH"
    for d in ["discovery","registry","messages","artifacts","presence","control","review","decisions","learning","interaction-model","integrity"]:
        (mesh/d).mkdir(parents=True,exist_ok=True)
    discovery={"schema":"org-agent-mesh/agent-discovery/v1","framework_version":FRAMEWORK_VERSION,"project_id":project_id,
      "active_protocol_versions":{"message":"v1","authority":"v1","evidence":"v1","continuity":"v1"},
      "bootstrap_order":["AGENT_DISCOVERY","PROJECT_MANIFEST","AUTHORITY","SOURCE_OF_TRUTH","ASSIGNMENT","RELEVANT_MESSAGES","RELEVANT_EVIDENCE","LANE_CLAIM"],
      "role_hierarchy":["ORCHESTRATOR","REVIEWER","SPECIALIST"],"active_project_state":"intake-v1",
      "communication_locations":{"messages":"../messages","presence":"../presence"},"evidence_locations":{"artifacts":"../artifacts"},
      "review_pipeline":["SPECIALIST","REVIEWER","ORCHESTRATOR"],"learning_protocol":"REVIEW_BEFORE_FRAMEWORK_CHANGE",
      "integrity_snapshot":"PENDING_INITIAL_HASH","configured_adapters":[ptype],"configured_tools":[],
      "mandatory_governance_rules":["LEAST_PRIVILEGE","NO_SELF_PROMOTION","NO_VOTING_AS_TRUTH","APPEND_ONLY_HISTORY","HUMAN_GATES_WHEN_CONFIGURED"],
      "declared_dependencies":[{"source_id":"project","reference":"PROJECT_MANIFEST.json"},{"source_id":"project","reference":"SOURCE_OF_TRUTH_MAP.json"},{"source_id":"project","reference":"INITIAL_WORK_BREAKDOWN.json"},{"source_id":"project","reference":"INITIAL_AGENT_REGISTRY.json"}]}
    _write_json(mesh/"discovery"/"AGENT_DISCOVERY.json",discovery)
    (mesh/"messages"/"README.md").write_text("# Initial Message Bus\n\nAppend-only immutable project messages live here. Corrections create superseding messages; existing records are not edited.\n",encoding="utf-8")
    (mesh/"messages"/"INDEX.jsonl").write_text("",encoding="utf-8")
    (mesh/"artifacts"/"README.md").write_text("# Initial Artifact Tree\n\nCreate material work under `<assignment_id>/<agent_id>/` with a manifest, report, evidence, tests/validation, output, proposed change if any, and checksums.\n",encoding="utf-8")
    for name in ["active_lanes","unresolved_blockers","accepted_state","latest_reviewed_lessons"]: _write_json(mesh/"control"/f"{name}.json",[])
    boot=root/"bootstrap"; boot.mkdir()
    for tier in ["ORCHESTRATOR","REVIEWER","SPECIALIST"]:
        (boot/f"{tier}.md").write_text(f"# {tier} project bootstrap\n\nRead ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json, PROJECT_MANIFEST.json, and only the evidence/messages relevant to your assignment. Validate integrity and authority before work.\n",encoding="utf-8")
    _write_json(root/"INITIAL_BOOTSTRAP_PACKAGES.json",{"packages":[f"bootstrap/{x}.md" for x in ["ORCHESTRATOR","REVIEWER","SPECIALIST"]],"status":"READY"})
    return root

def reconstruct_bootstrap_state(project_root):
    root=Path(project_root)
    required=["PROJECT_MANIFEST.json","SOURCE_OF_TRUTH_MAP.json","INITIAL_WORK_BREAKDOWN.json","INITIAL_AGENT_REGISTRY.json","ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json"]
    missing=[x for x in required if not (root/x).exists()]
    if missing: return {"ready":False,"missing":missing}
    manifest=json.loads((root/"PROJECT_MANIFEST.json").read_text())
    discovery=json.loads((root/"ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json").read_text())
    return {"ready":True,"project_id":manifest["project_id"],"problem_statement":manifest["problem_statement"],"project_type":manifest["project_type"],"active_project_state":discovery["active_project_state"],"authority":manifest["integration_authority"],"open_work":json.loads((root/"INITIAL_WORK_BREAKDOWN.json").read_text())}
