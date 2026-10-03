from .constants import CAPABILITIES

BASE_CAPABILITIES = {
    "ORCHESTRATOR": {
        "READ_SOURCE": True, "WRITE_WORKING_ARTIFACTS": True, "WRITE_ACCEPTED_STATE": True,
        "SEND_EXTERNAL_COMMUNICATION": False, "MODIFY_EXTERNAL_SYSTEM": False, "DELETE_DATA": False,
        "ACCESS_SENSITIVE_DATA": False, "APPROVE_RELEASE": True,
        "AUTHORIZE_FINANCIAL_ACTION": False, "AUTHORIZE_POLICY_CHANGE": False,
    },
    "REVIEWER": {
        "READ_SOURCE": True, "WRITE_WORKING_ARTIFACTS": True, "WRITE_ACCEPTED_STATE": False,
        "SEND_EXTERNAL_COMMUNICATION": False, "MODIFY_EXTERNAL_SYSTEM": False, "DELETE_DATA": False,
        "ACCESS_SENSITIVE_DATA": False, "APPROVE_RELEASE": False,
        "AUTHORIZE_FINANCIAL_ACTION": False, "AUTHORIZE_POLICY_CHANGE": False,
    },
    "SPECIALIST": {
        "READ_SOURCE": True, "WRITE_WORKING_ARTIFACTS": True, "WRITE_ACCEPTED_STATE": False,
        "SEND_EXTERNAL_COMMUNICATION": False, "MODIFY_EXTERNAL_SYSTEM": False, "DELETE_DATA": False,
        "ACCESS_SENSITIVE_DATA": False, "APPROVE_RELEASE": False,
        "AUTHORIZE_FINANCIAL_ACTION": False, "AUTHORIZE_POLICY_CHANGE": False,
    },
}

def capabilities_for(tier, explicit_grants=None):
    if tier not in BASE_CAPABILITIES:
        raise ValueError(f"Unknown authority tier: {tier}")
    result = dict(BASE_CAPABILITIES[tier])
    explicit_grants = explicit_grants or {}
    unknown = set(explicit_grants) - set(CAPABILITIES)
    if unknown:
        raise ValueError(f"Unknown capability keys: {sorted(unknown)}")
    result.update({k: bool(v) for k, v in explicit_grants.items()})
    return result

def has_capability(tier, capability, explicit_grants=None):
    if capability not in CAPABILITIES:
        raise ValueError(f"Unknown capability: {capability}")
    return capabilities_for(tier, explicit_grants).get(capability, False)

def require_capability(tier, capability, explicit_grants=None):
    if not has_capability(tier, capability, explicit_grants):
        raise PermissionError(f"{tier} lacks {capability}")
    return True

def peer_input_cannot_elevate(tier, proposed_capabilities):
    """Peer messages and learned lessons are advisory and cannot grant authority."""
    baseline = capabilities_for(tier)
    return {k: baseline[k] for k in CAPABILITIES}
