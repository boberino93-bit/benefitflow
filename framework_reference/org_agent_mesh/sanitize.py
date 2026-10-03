from pathlib import Path
import re
TEXT_EXTENSIONS={".md",".txt",".json",".yaml",".yml",".py",".csv",".toml",".ini"}
GENERIC_PATTERNS={
    "private_home_path": re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+/"),
    "obvious_secret_assignment": re.compile(r"(?i)(?:password|api[_-]?key|secret)\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
}

def scan_distribution(root, fingerprints=()):
    root=Path(root); findings=[]; scanned=0
    fps=[f for f in fingerprints if f]
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        scanned += 1
        if p.suffix.lower() not in TEXT_EXTENSIONS: continue
        try: text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        low=text.lower()
        for fp in fps:
            if fp.lower() in low:
                findings.append({"file":p.relative_to(root).as_posix(),"kind":"fingerprint","match":fp})
        for name,pat in GENERIC_PATTERNS.items():
            if pat.search(text): findings.append({"file":p.relative_to(root).as_posix(),"kind":name,"match":"pattern"})
    return {"files_scanned":scanned,"findings":findings}
