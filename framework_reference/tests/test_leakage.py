from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest
from org_agent_mesh.sanitize import scan_distribution
class LeakageTest(unittest.TestCase):
    def test_custom_fingerprint_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,"x.txt").write_text("synthetic-migration-fingerprint")
            result=scan_distribution(d,["synthetic-migration-fingerprint"])
            self.assertEqual(len(result["findings"]),1)
    def test_base_distribution_has_no_generic_secret_pattern(self):
        result=scan_distribution(ROOT)
        self.assertEqual(result["findings"],[])
