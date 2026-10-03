from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest
from org_agent_mesh.message_bus import append_message, supersede_message
BASE={"schema":"org-agent-mesh/message/v1","project_id":"p","timestamp_utc":"2026-01-01T00:00:00Z","from_agent":"a","from_role":"SPECIALIST","to":["r"],"kind":"FINDING","priority":"normal","subject":"x","summary":"x","applies_to_state":"v1","evidence":[],"artifacts":[],"reply_to":None,"supersedes":[],"requires_ack":False,"tags":[]}
class SupersessionTest(unittest.TestCase):
 def test_old_record_survives(self):
  with tempfile.TemporaryDirectory() as d:
   old=dict(BASE,id="m1"); p1=append_message(d,old)
   new=dict(BASE,id="m2",timestamp_utc="2026-01-01T00:01:00Z",summary="corrected")
   p2=supersede_message(d,old,new)
   self.assertTrue(p1.exists() and p2.exists())
   import json
   self.assertIn("m1",json.loads(p2.read_text())["supersedes"])
