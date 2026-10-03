from pathlib import Path
import json
from datetime import datetime, timezone

def append_presence(presence_dir, frame):
    required={"frame_id","agent_id","timestamp_utc","declared_state","lease_seconds","project_state"}
    missing=required-set(frame)
    if missing: raise ValueError(f"Presence frame missing: {sorted(missing)}")
    p=Path(presence_dir); p.mkdir(parents=True, exist_ok=True)
    out=p/f"{frame['timestamp_utc'].replace(':','-')}__{frame['frame_id']}.json"
    if out.exists(): raise FileExistsError("Presence frames are immutable")
    out.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return out

def derive_status(frame, now=None):
    state=frame.get("declared_state","UNKNOWN")
    if state in {"RELEASED","FAILED","BLOCKED","IDLE"}: return state
    now=now or datetime.now(timezone.utc)
    ts=datetime.fromisoformat(frame["timestamp_utc"].replace("Z","+00:00"))
    age=(now-ts).total_seconds()
    if age > int(frame["lease_seconds"]): return "LATE"
    return "ACTIVE" if state == "ACTIVE" else "UNKNOWN"
