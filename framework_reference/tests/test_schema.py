from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json, unittest
from org_agent_mesh.message_bus import validate_message
class SchemaTest(unittest.TestCase):
    def test_project_template_required_fields(self):
        schema=json.loads((ROOT/"schemas/project_manifest.schema.json").read_text())
        template=json.loads((ROOT/"PROJECT_TEMPLATE.json").read_text())
        self.assertEqual(sorted(set(schema["required"])-set(template)),[])
    def test_message_examples_validate(self):
        for p in (ROOT/"synthetic_examples/messages").glob("*.json"):
            validate_message(json.loads(p.read_text()))
    def test_agent_and_artifact_schema_have_required_contracts(self):
        for name in ["agent_record.schema.json","artifact_manifest.schema.json"]:
            schema=json.loads((ROOT/"schemas"/name).read_text())
            self.assertTrue(schema.get("required"))
