from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'tools' / 'generate_successor_package.py'


def main():
    for role in ('PRIMARY', 'MANAGER', 'RESEARCH'):
        subprocess.run([sys.executable, str(GENERATOR), role], check=True)


if __name__ == '__main__':
    main()
