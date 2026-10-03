from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import unittest
from datetime import datetime, timezone, timedelta
from org_agent_mesh.presence import derive_status
class PresenceTest(unittest.TestCase):
 def test_stale_active_worker_ages_to_late(self):
  now=datetime(2026,1,1,0,2,tzinfo=timezone.utc)
  f={"declared_state":"ACTIVE","timestamp_utc":"2026-01-01T00:00:00Z","lease_seconds":30}
  self.assertEqual(derive_status(f,now),"LATE")
