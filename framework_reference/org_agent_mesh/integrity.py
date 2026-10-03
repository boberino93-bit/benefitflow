from pathlib import Path
import hashlib

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def build_sha256sums(root, exclude=("SHA256SUMS.txt",)):
    root=Path(root); lines=[]
    for p in sorted(x for x in root.rglob("*") if x.is_file() and x.name not in exclude):
        lines.append(f"{sha256_file(p)}  {p.relative_to(root).as_posix()}")
    return "\n".join(lines)+"\n"

def verify_sha256sums(root, sums_path=None):
    root=Path(root); sums_path=Path(sums_path or root/"SHA256SUMS.txt")
    errors=[]
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, rel=line.split("  ",1)
        p=root/rel
        if not p.is_file(): errors.append(f"missing:{rel}")
        elif sha256_file(p)!=digest: errors.append(f"hash:{rel}")
    return errors
