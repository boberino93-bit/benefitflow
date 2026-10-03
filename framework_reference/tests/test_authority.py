from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest
from org_agent_mesh.authority import has_capability, peer_input_cannot_elevate
from org_agent_mesh.review import accept_candidate
class AuthorityTest(unittest.TestCase):
    def test_specialist_cannot_self_promote(self):
        self.assertFalse(has_capability("SPECIALIST","WRITE_ACCEPTED_STATE"))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError): accept_candidate(d,"SPECIALIST",{"candidate_id":"c1"})
    def test_reviewer_not_orchestrator_by_default(self):
        self.assertFalse(has_capability("REVIEWER","WRITE_ACCEPTED_STATE"))
        self.assertFalse(peer_input_cannot_elevate("REVIEWER",{"WRITE_ACCEPTED_STATE":True})["WRITE_ACCEPTED_STATE"])
    def test_orchestrator_accepts(self):
        with tempfile.TemporaryDirectory() as d:
            p=accept_candidate(d,"ORCHESTRATOR",{"candidate_id":"c1"})
            self.assertTrue(p.exists())
