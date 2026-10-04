from __future__ import annotations
from datetime import timedelta, timezone
from .coordination import AuthorizationError, ConflictError, PROJECT_ID, ProjectMode, canonical_payload_hash
from .durable_store import _SQLiteStoreBase, dump, iso, load, utc_now

class DurableCoordinationStore(_SQLiteStoreBase):
    """Durable project-scoped idempotency, leases, state, audit and outbox."""
    def apply_state_mutation(self,*,actor,resource_id,expected_version,value,correlation_id,causation_id,idempotency_key,outbox_topic=None,outbox_payload=None):
        self._actor(actor); self._text("resource_id",resource_id)
        if expected_version<0: raise ValueError("expected_version must be non-negative")
        now=utc_now(); action="STATE_WRITE"; eid=self._event_id(idempotency_key,action)
        with self._transaction() as c:
            self._require_active(c); replay=self._reserve(c,actor,idempotency_key,now)
            if replay is not None: return replay
            r=c.execute("SELECT version FROM versioned_state WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id)).fetchone(); current=int(r["version"]) if r else 0
            if current!=expected_version: raise ConflictError(f"stale write: expected {expected_version}, current {current}")
            version=current+1
            c.execute("INSERT INTO versioned_state VALUES(?,?,?,?,?) ON CONFLICT(project_id,resource_id) DO UPDATE SET version=excluded.version,value_json=excluded.value_json,updated_at=excluded.updated_at",(PROJECT_ID,resource_id,version,dump(value),iso(now)))
            self._audit(c,event_id=eid,actor=actor,action=action,resource_kind="state",resource_id=resource_id,correlation_id=correlation_id,causation_id=causation_id,idempotency_key=idempotency_key,outcome="COMMITTED",payload=value,metadata={"previous_version":current,"new_version":version},now=now)
            if outbox_topic is not None:
                self._text("outbox_topic",outbox_topic); payload=value if outbox_payload is None else outbox_payload
                c.execute("INSERT INTO outbox VALUES(NULL,?,?,?,?,?,?)",(PROJECT_ID,eid,outbox_topic,dump(payload),canonical_payload_hash(payload),iso(now)))
            result={"project_id":PROJECT_ID,"resource_id":resource_id,"version":version,"event_id":eid,"duplicate":False}; self._complete(c,idempotency_key,result,now); return result

    def read_state(self,resource_id):
        c=self._connect()
        try:
            r=c.execute("SELECT version,value_json FROM versioned_state WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id)).fetchone()
            return (0,None) if r is None else (int(r["version"]),load(r["value_json"]))
        finally: c.close()

    def claim_lease(self,*,actor,resource_id,ttl_seconds,correlation_id,causation_id,idempotency_key,now=None):
        self._actor(actor)
        if ttl_seconds<=0: raise ValueError("positive TTL required")
        now=(now or utc_now()).astimezone(timezone.utc); action="LEASE_CLAIM"; eid=self._event_id(idempotency_key,action)
        with self._transaction() as c:
            self._require_active(c); replay=self._reserve(c,actor,idempotency_key,now)
            if replay is not None: return replay
            r=c.execute("SELECT holder_instance_id,expires_at,version FROM leases WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id)).fetchone(); version=1
            if r:
                from datetime import datetime
                if datetime.fromisoformat(r["expires_at"]).astimezone(timezone.utc)>now and r["holder_instance_id"]!=actor.agent_instance_id: raise ConflictError("active durable lease exists")
                version=int(r["version"])+1
            expires=now+timedelta(seconds=ttl_seconds)
            c.execute("INSERT INTO leases VALUES(?,?,?,?,?,?) ON CONFLICT(project_id,resource_id) DO UPDATE SET holder_instance_id=excluded.holder_instance_id,expires_at=excluded.expires_at,version=excluded.version,updated_at=excluded.updated_at",(PROJECT_ID,resource_id,actor.agent_instance_id,iso(expires),version,iso(now)))
            payload={"holder_instance_id":actor.agent_instance_id,"expires_at":iso(expires),"version":version}
            self._audit(c,event_id=eid,actor=actor,action=action,resource_kind="lease",resource_id=resource_id,correlation_id=correlation_id,causation_id=causation_id,idempotency_key=idempotency_key,outcome="CLAIMED",payload=payload,metadata={},now=now)
            result={"project_id":PROJECT_ID,"resource_id":resource_id,**payload,"event_id":eid,"duplicate":False}; self._complete(c,idempotency_key,result,now); return result

    def renew_lease(self,*,actor,resource_id,ttl_seconds,correlation_id,causation_id,idempotency_key,now=None):
        from datetime import datetime
        self._actor(actor)
        if ttl_seconds<=0: raise ValueError("positive TTL required")
        now=(now or utc_now()).astimezone(timezone.utc); action="LEASE_RENEW"; eid=self._event_id(idempotency_key,action)
        with self._transaction() as c:
            self._require_active(c); replay=self._reserve(c,actor,idempotency_key,now)
            if replay is not None: return replay
            r=c.execute("SELECT holder_instance_id,expires_at,version FROM leases WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id)).fetchone()
            if not r or r["holder_instance_id"]!=actor.agent_instance_id or datetime.fromisoformat(r["expires_at"]).astimezone(timezone.utc)<=now: raise ConflictError("lease is missing, expired, or held by another instance")
            version=int(r["version"])+1; expires=now+timedelta(seconds=ttl_seconds)
            c.execute("UPDATE leases SET expires_at=?,version=?,updated_at=? WHERE project_id=? AND resource_id=?",(iso(expires),version,iso(now),PROJECT_ID,resource_id))
            payload={"expires_at":iso(expires),"version":version}; self._audit(c,event_id=eid,actor=actor,action=action,resource_kind="lease",resource_id=resource_id,correlation_id=correlation_id,causation_id=causation_id,idempotency_key=idempotency_key,outcome="RENEWED",payload=payload,metadata={},now=now)
            result={"project_id":PROJECT_ID,"resource_id":resource_id,**payload,"event_id":eid,"duplicate":False}; self._complete(c,idempotency_key,result,now); return result

    def release_lease(self,*,actor,resource_id,correlation_id,causation_id,idempotency_key):
        self._actor(actor); now=utc_now(); action="LEASE_RELEASE"; eid=self._event_id(idempotency_key,action)
        with self._transaction() as c:
            self._require_active(c); replay=self._reserve(c,actor,idempotency_key,now)
            if replay is not None: return replay
            r=c.execute("SELECT holder_instance_id FROM leases WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id)).fetchone()
            if r and r["holder_instance_id"]!=actor.agent_instance_id: raise AuthorizationError("only the holder instance may release a durable lease")
            released=r is not None
            if released: c.execute("DELETE FROM leases WHERE project_id=? AND resource_id=?",(PROJECT_ID,resource_id))
            payload={"released":released}; self._audit(c,event_id=eid,actor=actor,action=action,resource_kind="lease",resource_id=resource_id,correlation_id=correlation_id,causation_id=causation_id,idempotency_key=idempotency_key,outcome="RELEASED" if released else "NOOP",payload=payload,metadata={},now=now)
            result={"project_id":PROJECT_ID,"resource_id":resource_id,**payload,"event_id":eid,"duplicate":False}; self._complete(c,idempotency_key,result,now); return result

    def set_project_mode(self,*,requester,mode,expected_version,human_approved,correlation_id,causation_id,idempotency_key):
        self._actor(requester)
        if requester.role!="PRIMARY": raise AuthorizationError("only Primary may apply durable project control mode")
        if not human_approved: raise AuthorizationError("explicit human approval required for project control mode")
        mode=ProjectMode(mode); now=utc_now(); action="PROJECT_MODE_SET"; eid=self._event_id(idempotency_key,action)
        with self._transaction() as c:
            replay=self._reserve(c,requester,idempotency_key,now)
            if replay is not None: return replay
            r=c.execute("SELECT mode,version FROM project_control WHERE project_id=?",(PROJECT_ID,)).fetchone(); current=int(r["version"])
            if current!=expected_version: raise ConflictError(f"stale project control write: expected {expected_version}, current {current}")
            version=current+1; c.execute("UPDATE project_control SET mode=?,version=?,updated_at=? WHERE project_id=?",(mode.value,version,iso(now),PROJECT_ID))
            payload={"previous_mode":r["mode"],"mode":mode.value,"version":version}; self._audit(c,event_id=eid,actor=requester,action=action,resource_kind="project_control",resource_id=PROJECT_ID,correlation_id=correlation_id,causation_id=causation_id,idempotency_key=idempotency_key,outcome="COMMITTED",payload=payload,metadata={"human_approved":True},now=now)
            result={"project_id":PROJECT_ID,**payload,"event_id":eid,"duplicate":False}; self._complete(c,idempotency_key,result,now); return result

    def pending_outbox(self,limit=100):
        if limit<=0: raise ValueError("limit must be positive")
        c=self._connect()
        try:
            rows=c.execute("SELECT o.seq,o.event_id,o.topic,o.payload_json,o.payload_hash,o.created_at FROM outbox o LEFT JOIN outbox_delivery d ON d.project_id=o.project_id AND d.event_id=o.event_id WHERE o.project_id=? AND d.event_id IS NULL ORDER BY o.seq LIMIT ?",(PROJECT_ID,limit)).fetchall()
            return [{"seq":int(r["seq"]),"event_id":r["event_id"],"topic":r["topic"],"payload":load(r["payload_json"]),"payload_hash":r["payload_hash"],"created_at":r["created_at"]} for r in rows]
        finally: c.close()

    def acknowledge_outbox(self,*,event_id,consumer_id,delivered_at=None):
        delivered_at=(delivered_at or utc_now()).astimezone(timezone.utc)
        with self._transaction() as c:
            if c.execute("SELECT 1 FROM outbox WHERE project_id=? AND event_id=?",(PROJECT_ID,event_id)).fetchone() is None: raise KeyError("unknown outbox event")
            return c.execute("INSERT OR IGNORE INTO outbox_delivery VALUES(NULL,?,?,?,?)",(PROJECT_ID,event_id,consumer_id,iso(delivered_at))).rowcount==1
