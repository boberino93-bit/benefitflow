def claim_lane(existing_claims, claim, allow_replication=False):
    required={"lane_id","assignment","scope","starting_project_state","expected_output","dependencies","possible_overlap","current_status","agent_id"}
    missing=required-set(claim)
    if missing:
        raise ValueError(f"Lane claim missing: {sorted(missing)}")
    active={"OPEN","ACTIVE","BLOCKED"}
    conflicts=[c for c in existing_claims if c.get("lane_id")==claim["lane_id"] and c.get("current_status") in active and c.get("agent_id")!=claim["agent_id"]]
    if conflicts and not allow_replication:
        raise RuntimeError("Active lane already claimed; reconcile overlap or explicitly authorize independent replication")
    out=dict(claim)
    out["replication_mode"]=bool(allow_replication and conflicts)
    return out
