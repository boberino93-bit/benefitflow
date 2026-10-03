#!/usr/bin/env python3
from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.successor import create_successor_package
p=argparse.ArgumentParser(); p.add_argument("project"); p.add_argument("output"); a=p.parse_args()
print(create_successor_package(a.project,a.output))
