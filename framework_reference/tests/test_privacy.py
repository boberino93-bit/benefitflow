from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest
from org_agent_mesh.initializer import initialize_project
from org_agent_mesh.successor import create_successor_package
class PrivacyTest(unittest.TestCase):
 def test_instance_interaction_record_not_copied_to_successor(self):
  with tempfile.TemporaryDirectory() as d:
   p=initialize_project("Improve a workflow.",d,"Workflow")
   private=p/"ORG_AGENT_MESH/interaction-model/preferences.json"
   private.write_text('{"reporting_preference":"instance-only"}')
   out=Path(d)/"successor"; create_successor_package(p,out)
   self.assertFalse((out/"ORG_AGENT_MESH/interaction-model/preferences.json").exists())
   self.assertFalse((ROOT/"interaction-model").exists())
