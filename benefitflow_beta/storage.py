from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

_DB = Path(__file__).resolve().parent.parent / "beta_state.sqlite3"
_LOCK = Lock()


def init_db() -> None:
    with sqlite3.connect(_DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)")


def put(key: str, value: dict[str, Any]) -> None:
    init_db()
    payload = json.dumps(value, default=str)
    with _LOCK, sqlite3.connect(_DB) as conn:
        conn.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, payload))
        conn.commit()


def get(key: str) -> dict[str, Any] | None:
    init_db()
    with sqlite3.connect(_DB) as conn:
        row = conn.execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None
