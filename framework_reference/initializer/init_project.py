#!/usr/bin/env python3
from pathlib import Path
import argparse, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from org_agent_mesh.initializer import initialize_project

def main():
    p=argparse.ArgumentParser(description="Initialize a governed multi-agent project from a sparse idea.")
    p.add_argument("--idea",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--name")
    p.add_argument("--domain",default="UNKNOWN")
    a=p.parse_args()
    print(initialize_project(a.idea,a.output,a.name,a.domain))
if __name__=="__main__": main()
