#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.sanitize import scan_distribution
result=scan_distribution(ROOT)
print(json.dumps(result,indent=2))
raise SystemExit(1 if result["findings"] else 0)
