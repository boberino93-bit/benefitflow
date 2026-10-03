from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.lanes import claim_lane
class LaneTest(unittest.TestCase):
    def test_duplicate_active_lane_requires_explicit_replication(self):
        base={"lane_id":"lane-a","assignment":"x","scope":"x","starting_project_state":"v1","expected_output":"x","dependencies":[],"possible_overlap":[],"current_status":"ACTIVE","agent_id":"a"}
        with self.assertRaises(RuntimeError): claim_lane([base],dict(base,agent_id="b"))
        out=claim_lane([base],dict(base,agent_id="b"),allow_replication=True)
        self.assertTrue(out["replication_mode"])
