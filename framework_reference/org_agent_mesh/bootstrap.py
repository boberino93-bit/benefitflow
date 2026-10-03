from pathlib import Path
import hashlib

def _sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def verify_declared_dependency_closure(discovery, source_roots):
    """Resolve every declared dependency against an explicit source root.

    No path guessing or fallback remapping is allowed. Returns a structured
    result; callers should fail closed when `closed` is false.
    """
    failures=[]; resolved=[]
    for dep in discovery.get('declared_dependencies',[]):
        source_id=dep.get('source_id'); ref=dep.get('reference')
        if not source_id or not ref:
            failures.append({'dependency':dep,'reason':'MALFORMED_DEPENDENCY'}); continue
        root=source_roots.get(source_id)
        if root is None:
            failures.append({'dependency':dep,'reason':'UNKNOWN_SOURCE'}); continue
        root=Path(root).resolve(); target=(root/ref).resolve()
        try: target.relative_to(root)
        except ValueError:
            failures.append({'dependency':dep,'reason':'OUTSIDE_SOURCE_ROOT'}); continue
        if not target.is_file():
            failures.append({'dependency':dep,'reason':'MISSING'}); continue
        expected=dep.get('sha256')
        actual=_sha256(target) if expected else None
        if expected and actual.lower()!=expected.lower():
            failures.append({'dependency':dep,'reason':'HASH_MISMATCH','actual_sha256':actual}); continue
        resolved.append({'source_id':source_id,'reference':ref,'sha256':actual})
    return {'closed':not failures,'resolved':resolved,'failures':failures}
