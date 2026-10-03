from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import unittest
from org_agent_mesh.continuity import evaluate_continuity
class ContinuityTest(unittest.TestCase):
 def test_changed_requirement_marks_dependent_output(self):
  prev=[{"item_id":"training-guide","dependencies":["requirement-a"],"evidence_refs":["ev1"]},{"item_id":"unrelated","dependencies":[],"evidence_refs":[]}]
  rows=evaluate_continuity(prev,{"change_id":"chg1","affects":["requirement-a"]})
  self.assertEqual(rows[0]["result"],"REVALIDATION_REQUIRED")
  self.assertFalse(rows[1]["validation_required"])
