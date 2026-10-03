from pathlib import Path
import json
from .authority import require_capability
from .constants import REVIEW_DISPOSITIONS

def make_review_disposition(candidate_id, reviewer_id, disposition, rationale, evidence_refs=None):
    if disposition not in REVIEW_DISPOSITIONS: raise ValueError("Unsupported review disposition")
    return {"candidate_id":candidate_id,"reviewer_id":reviewer_id,"disposition":disposition,
            "rationale":rationale,"evidence_refs":evidence_refs or [],"is_final_acceptance":False}

def accept_candidate(accepted_state_dir, tier, candidate, explicit_grants=None):
    require_capability(tier,"WRITE_ACCEPTED_STATE",explicit_grants)
    p=Path(accepted_state_dir); p.mkdir(parents=True,exist_ok=True)
    out=p/f"{candidate['candidate_id']}.json"
    if out.exists(): raise FileExistsError("Accepted-state records are immutable; supersede instead")
    data=dict(candidate); data["accepted_by_tier"]=tier
    out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return out
