from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

def sha256(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    snap=Path(sys.argv[1])
    manifest_path=snap/'SNAPSHOT_MANIFEST.json'
    m=json.loads(manifest_path.read_text())
    assert m['project_id']=='benefitflow'
    assert m['AGENTBUS_SNAPSHOT_COMPLETE'] is True
    for rec in m['files']:
        p=snap/rec['packaged']
        assert p.exists(), rec['packaged']
        assert p.stat().st_size==rec['bytes'], rec['packaged']
        assert sha256(p)==rec['sha256'], rec['packaged']
    print(f"verified {len(m['files'])} files; {m['message_count']} forum messages")
if __name__=='__main__': main()
