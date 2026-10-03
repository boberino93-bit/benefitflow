def reconciliation_plan(contradiction_id, claim_a, claim_b):
    return {
        "contradiction_id": contradiction_id,
        "method": "EVIDENCE_RECONCILIATION",
        "steps": [
            "COMPARE_APPLICABILITY_AND_PROJECT_STATE",
            "COMPARE_PROVENANCE",
            "COMPARE_EVIDENCE_CLASS",
            "COMPARE_FRESHNESS",
            "INSPECT_RAW_EVIDENCE",
            "RUN_CHEAPEST_DECISIVE_VALIDATION_IF_AVAILABLE",
            "REVIEWER_RECONCILIATION",
            "ORCHESTRATOR_CONFIRMATION_FOR_ACCEPTED_STATE_CHANGE",
        ],
        "claim_a": claim_a, "claim_b": claim_b,
        "prohibited_resolution_basis": ["AGENT_VOTE", "MAJORITY_COUNT", "CONFIDENCE_WORDING_ONLY"],
    }
