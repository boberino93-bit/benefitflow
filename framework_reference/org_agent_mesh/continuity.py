def evaluate_continuity(previous_items, change):
    affected=set(change.get("affects",[]))
    rows=[]
    for item in previous_items:
        item_id=item["item_id"]
        impacted=item_id in affected or bool(set(item.get("dependencies",[])) & affected)
        rows.append({
            "previous_item":item_id,
            "change_id":change["change_id"],
            "potentially_affected":impacted,
            "validation_required":impacted,
            "result":"REVALIDATION_REQUIRED" if impacted else "UNAFFECTED_BY_DECLARED_SCOPE",
            "invalidated_prior_evidence":item.get("evidence_refs",[]) if impacted else [],
            "replacement_evidence":[],
        })
    return rows
