from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import unittest
from org_agent_mesh.contradiction import reconciliation_plan
class ContradictionTest(unittest.TestCase):
 def test_no_voting_and_full_reconciliation_path(self):
  p=reconciliation_plan("c",{}, {})
  self.assertEqual(p["method"],"EVIDENCE_RECONCILIATION")
  self.assertIn("COMPARE_PROVENANCE",p["steps"])
  self.assertIn("REVIEWER_RECONCILIATION",p["steps"])
  self.assertIn("ORCHESTRATOR_CONFIRMATION_FOR_ACCEPTED_STATE_CHANGE",p["steps"])
  self.assertIn("AGENT_VOTE",p["prohibited_resolution_basis"])
