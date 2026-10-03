REQUIRED_EVIDENCE_FIELDS = {
    "evidence_id", "source", "applies_to_state", "evidence_class", "collection_method",
    "confidence_limitations", "reproducibility", "artifact_reference", "independently_verified"
}

def validate_evidence(record):
    missing = sorted(REQUIRED_EVIDENCE_FIELDS - set(record))
    if missing:
        raise ValueError(f"Evidence record missing: {missing}")
    return True
