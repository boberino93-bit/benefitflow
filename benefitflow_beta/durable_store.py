from __future__ import annotations
import json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from .coordination import AgentIdentity, AuthorizationError, ConflictError, PROJECT_ID, ProjectMode, canonical_payload_hash

SCHEMA_VERSION = "benefitflow/durable-coordination/v1"
def utc_now(): return datetime.now(timezone.utc)
def iso(v): return v.astimezone(timezone.utc).isoformat()
def dump(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def load(v): return None if v is None else json.loads(v)

class _SQLiteStoreBase:
    def __init__(self,database_path:str|Path):
        self.database_path=Path(database_path)
        if str(self.database_path)!=" :memory:".strip(): self.database_path.parent.mkdir(parents=True,exist_ok=True)
        self._initialize()
    def _connect(self):
        c=sqlite3.connect(str(self.database_path),timeout=30,isolation_level=None); c.row_factory=sqlite3.Row
        c.execute("PRAGMA busy_timeout=30000"); c.execute("PRAGMA foreign_keys=ON"); return c
    @contextmanager
    def _transaction(self)->Iterator[sqlite3.Connection]:
        c=self._connect()
        try: c.execute("BEGIN IMMEDIATE"); yield c; c.execute("COMMIT")
        except Exception:
            if c.in_transaction: c.execute("ROLLBACK")
            raise
        finally: c.close()
    def _initialize(self):
        c=self._connect()
        try:
            if str(self.database_path)!=" :memory:".strip(): c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA synchronous=FULL")
            c.executescript("""
CREATE TABLE IF NOT EXISTS coordination_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project_control(project_id TEXT PRIMARY KEY,mode TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS idempotency(project_id TEXT NOT NULL,idempotency_key TEXT NOT NULL,owner_instance_id TEXT NOT NULL,status TEXT NOT NULL,result_json TEXT,reserved_at TEXT NOT NULL,expires_at TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(project_id,idempotency_key));
CREATE TABLE IF NOT EXISTS leases(project_id TEXT NOT NULL,resource_id TEXT NOT NULL,holder_instance_id TEXT NOT NULL,expires_at TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(project_id,resource_id));
CREATE TABLE IF NOT EXISTS versioned_state(project_id TEXT NOT NULL,resource_id TEXT NOT NULL,version INTEGER NOT NULL,value_json TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(project_id,resource_id));
CREATE TABLE IF NOT EXISTS audit_log(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL,event_id TEXT NOT NULL,actor_instance_id TEXT NOT NULL,action TEXT NOT NULL,resource_kind TEXT NOT NULL,resource_id TEXT NOT NULL,correlation_id TEXT NOT NULL,causation_id TEXT NOT NULL,idempotency_key TEXT NOT NULL,outcome TEXT NOT NULL,payload_hash TEXT NOT NULL,metadata_json TEXT NOT NULL,previous_hash TEXT NOT NULL,record_hash TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(project_id,event_id));
CREATE TABLE IF NOT EXISTS outbox(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL,event_id TEXT NOT NULL,topic TEXT NOT NULL,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(project_id,event_id));
CREATE TABLE IF NOT EXISTS outbox_delivery(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL,event_id TEXT NOT NULL,consumer_id TEXT NOT NULL,delivered_at TEXT NOT NULL,UNIQUE(project_id,event_id),FOREIGN KEY(project_id,event_id) REFERENCES outbox(project_id,event_id));
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS outbox_no_update BEFORE UPDATE ON outbox BEGIN SELECT RAISE(ABORT,'outbox is append-only'); END;
CREATE TRIGGER IF NOT EXISTS outbox_no_delete BEFORE DELETE ON outbox BEGIN SELECT RAISE(ABORT,'outbox is append-only'); END;
CREATE TRIGGER IF NOT EXISTS outbox_delivery_no_update BEFORE UPDATE ON outbox_delivery BEGIN SELECT RAISE(ABORT,'outbox delivery receipts are append-only'); END;
CREATE TRIGGER IF NOT EXISTS outbox_delivery_no_delete BEFORE DELETE ON outbox_delivery BEGIN SELECT RAISE(ABORT,'outbox delivery receipts are append-only'); END;
""")
            now=iso(utc_now()); c.execute("INSERT OR IGNORE INTO coordination_metadata VALUES('schema_version',?)",(SCHEMA_VERSION,))
            if c.execute("SELECT value FROM coordination_metadata WHERE key='schema_version'").fetchone()["value"]!=SCHEMA_VERSION: raise RuntimeError("durable coordination schema mismatch")
            c.execute("INSERT OR IGNORE INTO project_control VALUES(?,?,0,?)",(PROJECT_ID,ProjectMode.ACTIVE.value,now))
        finally: c.close()
    @staticmethod
    def _actor(a:AgentIdentity):
        if a.project_id!=PROJECT_ID: raise AuthorizationError("foreign durable coordination actor")
    @staticmethod
    def _text(name,value):
        if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} required")
    @staticmethod
    def _event_id(key,action): return canonical_payload_hash({"project_id":PROJECT_ID,"idempotency_key":key,"action":action})
    def mode(self):
        c=self._connect()
        try:
            r=c.execute("SELECT mode,version FROM project_control WHERE project_id=?",(PROJECT_ID,)).fetchone()
            if not r: raise RuntimeError("missing BenefitFlow project control row")
            return ProjectMode(r["mode"]),int(r["version"])
        finally: c.close()
    def _require_active(self,c):
        r=c.execute("SELECT mode FROM project_control WHERE project_id=?",(PROJECT_ID,)).fetchone()
        if not r or r["mode"]!=ProjectMode.ACTIVE.value: raise AuthorizationError(f"durable project mutations disabled while mode={r['mode'] if r else 'MISSING'}")
    def _reserve(self,c,a,key,now,ttl=300):
        self._actor(a); self._text("idempotency_key",key)
        r=c.execute("SELECT status,result_json,expires_at FROM idempotency WHERE project_id=? AND idempotency_key=?",(PROJECT_ID,key)).fetchone()
        if r:
            if r["status"]=="COMPLETE": return {**(load(r["result_json"]) or {}),"duplicate":True}
            if datetime.fromisoformat(r["expires_at"]).astimezone(timezone.utc)>now: raise ConflictError("idempotent operation already in progress")
            c.execute("DELETE FROM idempotency WHERE project_id=? AND idempotency_key=?",(PROJECT_ID,key))
        c.execute("INSERT INTO idempotency VALUES(?,?,?,'PENDING',NULL,?,?,?)",(PROJECT_ID,key,a.agent_instance_id,iso(now),iso(now+timedelta(seconds=ttl)),iso(now)))
    def _complete(self,c,key,result,now):
        if c.execute("UPDATE idempotency SET status='COMPLETE',result_json=?,updated_at=? WHERE project_id=? AND idempotency_key=? AND status='PENDING'",(dump(result),iso(now),PROJECT_ID,key)).rowcount!=1: raise ConflictError("idempotency reservation lost")
    def _audit(self,c,*,event_id,actor,action,resource_kind,resource_id,correlation_id,causation_id,idempotency_key,outcome,payload,metadata,now):
        prev=c.execute("SELECT record_hash FROM audit_log WHERE project_id=? ORDER BY seq DESC LIMIT 1",(PROJECT_ID,)).fetchone(); ph=prev["record_hash"] if prev else "GENESIS"; p_hash=canonical_payload_hash(payload)
        record={"project_id":PROJECT_ID,"event_id":event_id,"actor_instance_id":actor.agent_instance_id,"action":action,"resource_kind":resource_kind,"resource_id":resource_id,"correlation_id":correlation_id,"causation_id":causation_id,"idempotency_key":idempotency_key,"outcome":outcome,"payload_hash":p_hash,"metadata":metadata,"previous_hash":ph,"created_at":iso(now)}
        c.execute("INSERT INTO audit_log(project_id,event_id,actor_instance_id,action,resource_kind,resource_id,correlation_id,causation_id,idempotency_key,outcome,payload_hash,metadata_json,previous_hash,record_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(PROJECT_ID,event_id,actor.agent_instance_id,action,resource_kind,resource_id,correlation_id,causation_id,idempotency_key,outcome,p_hash,dump(metadata),ph,canonical_payload_hash(record),iso(now)))
    def audit_records(self):
        c=self._connect()
        try: return [dict(r) for r in c.execute("SELECT * FROM audit_log WHERE project_id=? ORDER BY seq",(PROJECT_ID,)).fetchall()]
        finally: c.close()
    def verify_integrity(self):
        c=self._connect()
        try:
            prev="GENESIS"; audits=c.execute("SELECT * FROM audit_log WHERE project_id=? ORDER BY seq",(PROJECT_ID,)).fetchall()
            for r in audits:
                if r["previous_hash"]!=prev: raise ConflictError("audit hash-chain discontinuity")
                record={"project_id":r["project_id"],"event_id":r["event_id"],"actor_instance_id":r["actor_instance_id"],"action":r["action"],"resource_kind":r["resource_kind"],"resource_id":r["resource_id"],"correlation_id":r["correlation_id"],"causation_id":r["causation_id"],"idempotency_key":r["idempotency_key"],"outcome":r["outcome"],"payload_hash":r["payload_hash"],"metadata":load(r["metadata_json"]),"previous_hash":r["previous_hash"],"created_at":r["created_at"]}
                if canonical_payload_hash(record)!=r["record_hash"]: raise ConflictError("audit record hash mismatch")
                prev=r["record_hash"]
            outbox=c.execute("SELECT event_id,payload_json,payload_hash FROM outbox WHERE project_id=? ORDER BY seq",(PROJECT_ID,)).fetchall()
            for r in outbox:
                if canonical_payload_hash(load(r["payload_json"]))!=r["payload_hash"]: raise ConflictError(f"outbox payload hash mismatch: {r['event_id']}")
            return {"project_id":PROJECT_ID,"schema_version":SCHEMA_VERSION,"audit_records":len(audits),"outbox_records":len(outbox),"audit_head":prev,"valid":True}
        finally: c.close()
    def foreign_row_counts(self):
        c=self._connect()
        try: return {t:int(c.execute(f"SELECT COUNT(*) n FROM {t} WHERE project_id<>?",(PROJECT_ID,)).fetchone()["n"]) for t in ("idempotency","leases","versioned_state","audit_log","outbox")}
        finally: c.close()
