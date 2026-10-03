from pathlib import Path
import json, re
from datetime import datetime, timezone
from .constants import MESSAGE_KINDS

REQUIRED = {"schema","id","project_id","timestamp_utc","from_agent","from_role","to","kind","priority","subject","summary","applies_to_state","evidence","artifacts","reply_to","supersedes","requires_ack","tags"}

def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "record"

def validate_message(message):
    missing = sorted(REQUIRED - set(message))
    if missing: raise ValueError(f"Message missing fields: {missing}")
    if message["kind"] not in MESSAGE_KINDS: raise ValueError("Unsupported message kind")
    if message["priority"] not in {"normal","high","critical"}: raise ValueError("Unsupported priority")
    if not isinstance(message["to"], list): raise ValueError("to must be a list")
    if not isinstance(message["supersedes"], list): raise ValueError("supersedes must be a list")
    return True

def append_message(messages_dir, message):
    validate_message(message)
    d=Path(messages_dir); d.mkdir(parents=True, exist_ok=True)
    p=d/f"{_safe(message['timestamp_utc'])}__{_safe(message['id'])}.json"
    if p.exists(): raise FileExistsError(f"Immutable message already exists: {p.name}")
    p.write_text(json.dumps(message, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return p

def supersede_message(messages_dir, old_message, replacement):
    replacement=dict(replacement)
    replacement.setdefault("supersedes", [])
    if old_message["id"] not in replacement["supersedes"]:
        replacement["supersedes"].append(old_message["id"])
    replacement["kind"]="SUPERSESSION"
    return append_message(messages_dir, replacement)

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
