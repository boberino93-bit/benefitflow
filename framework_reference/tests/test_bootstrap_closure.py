from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.bootstrap import verify_declared_dependency_closure
class BootstrapClosureTest(unittest.TestCase):
    def test_missing_declared_dependency_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'present.txt').write_text('ok')
            discovery={'declared_dependencies':[{'source_id':'project','reference':'present.txt'},{'source_id':'project','reference':'missing.txt'}]}
            r=verify_declared_dependency_closure(discovery,{'project':d})
            self.assertFalse(r['closed'])
            self.assertEqual(r['failures'][0]['reason'],'MISSING')
    def test_all_declared_dependencies_resolve(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'present.txt').write_text('ok')
            discovery={'declared_dependencies':[{'source_id':'project','reference':'present.txt'}]}
            self.assertTrue(verify_declared_dependency_closure(discovery,{'project':d})['closed'])
