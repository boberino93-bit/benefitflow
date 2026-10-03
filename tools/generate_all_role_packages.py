from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'tools' / 'generate_successor_package.py'
VERIFIER = ROOT / 'tools' / 'verify_role_package_enhancement_sync.py'


def main():
    subprocess.run([sys.executable, str(VERIFIER)], check=True)

    generated: list[str] = []
    for role in ('PRIMARY', 'MANAGER', 'RESEARCH'):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), role],
            check=True,
            capture_output=True,
            text=True,
        )
        package_path = result.stdout.strip().splitlines()[-1]
        generated.append(package_path)

    verify_cmd = [sys.executable, str(VERIFIER)]
    for package in generated:
        verify_cmd.extend(['--package', package])
    subprocess.run(verify_cmd, check=True)

    for package in generated:
        print(package)


if __name__ == '__main__':
    main()
