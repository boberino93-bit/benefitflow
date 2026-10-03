#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.integrity import verify_sha256sums
errors=verify_sha256sums(ROOT)
if errors:
    print("FAIL", *errors, sep="\n"); raise SystemExit(1)
print("PASS: package hashes verified")
