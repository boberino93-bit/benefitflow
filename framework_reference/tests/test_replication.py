from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest, json
from org_agent_mesh.initializer import initialize_project
from org_agent_mesh.successor import create_successor_package
from org_agent_mesh.integrity import verify_sha256sums
class ReplicationTest(unittest.TestCase):
 def test_successor_contains_bootstrap_contracts(self):
  with tempfile.TemporaryDirectory() as d:
   p=initialize_project("Investigate service delays and recommend an implementation.",d,"Service Delay Study")
   out=Path(d)/"successor"
   create_successor_package(p,out)
   m=json.loads((out/"SUCCESSOR_MANIFEST.json").read_text())
   self.assertTrue((out/m["required_communication_schema"]).exists())
   self.assertTrue((out/m["required_bootstrap_root"]).exists())
   self.assertTrue((out/m["required_protocol_root"]).exists())
   self.assertEqual(verify_sha256sums(out),[])
