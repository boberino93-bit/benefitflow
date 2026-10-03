from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile, unittest
from org_agent_mesh.initializer import initialize_project, reconstruct_bootstrap_state
class BootstrapTest(unittest.TestCase):
    def test_sparse_idea_bootstraps(self):
        with tempfile.TemporaryDirectory() as d:
            p=initialize_project("We need to improve supplier intake.",d,"Intake Improvement")
            state=reconstruct_bootstrap_state(p)
            self.assertTrue(state["ready"])
            self.assertEqual(state["project_type"],"PROCESS_IMPROVEMENT_PROJECT")
            for rel in ["PROJECT_MANIFEST.json","PROJECT_CHARTER.md","ASSUMPTIONS_LOG.json","OPEN_QUESTIONS.json","SOURCE_OF_TRUTH_MAP.json","INITIAL_RISK_REGISTER.json","INITIAL_WORK_BREAKDOWN.json","INITIAL_AGENT_REGISTRY.json","INITIAL_REVIEW_PLAN.json","INITIAL_VALIDATION_PLAN.json","INITIAL_DECISION_LOG.json","INITIAL_BOOTSTRAP_PACKAGES.json","PROJECT_PACKAGE_MANIFEST.json"]:
                self.assertTrue((p/rel).exists(),rel)
            for rel in ["ORG_AGENT_MESH/messages","ORG_AGENT_MESH/artifacts"]:
                self.assertTrue((p/rel).exists(),rel)
