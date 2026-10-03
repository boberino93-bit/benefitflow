import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_recursive_backup_builds_complete_snapshot():
    r=subprocess.run([sys.executable,str(ROOT/'tools/build_recursive_backup.py')],check=True,capture_output=True,text=True)
    backup=Path(r.stdout.strip())
    snap=backup/'DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT'
    m=json.loads((snap/'SNAPSHOT_MANIFEST.json').read_text())
    assert m['project_id']=='benefitflow'
    assert m['AGENTBUS_SNAPSHOT_COMPLETE'] is True
    assert m['message_count'] >= 2
    subprocess.run([sys.executable,str(ROOT/'tools/verify_recursive_backup.py'),str(snap)],check=True)

def test_successor_package_contains_recursive_snapshot():
    r=subprocess.run([sys.executable,str(ROOT/'tools/generate_successor_package.py'),'PRIMARY'],check=True,capture_output=True,text=True)
    out=Path(r.stdout.strip())
    assert (out/'SUCCESSOR_MANIFEST.json').exists()
    assert (out/'DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/SNAPSHOT_MANIFEST.json').exists()
    m=json.loads((out/'SUCCESSOR_MANIFEST.json').read_text())
    assert m['project_id']=='benefitflow'
    assert m['requires_revalidation'] is True
    assert m['authority_granted'] is False
