from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; BUS=ROOT/'BenefitFlow-AgentBus'
ROLES=('PRIMARY','MANAGER','RESEARCH'); PROTOCOL='3.1.0'; REPO_ID=1403645790; PACKAGE_SCHEMA='benefitflow/successor-package/v8'
IDENTITY=(ROOT/'AGENT_BOOTSTRAP.json',ROOT/'AGENT_BOOTSTRAP.md',ROOT/'NEW_PROJECT_BOOTSTRAP.json',ROOT/'REPOSITORY_BOOTSTRAP.md',BUS/'PROJECT_SCOPE_SELECTION_GATE_V1.md',BUS/'control/PROJECT_IDENTITY_LOCK.json',BUS/'control/PROJECT_SCOPE_BINDING.json',BUS/'control/GITHUB_REPOSITORY_BINDING.json',BUS/'discovery/AGENT_DISCOVERY.json')
PROTOCOL_FILES=(BUS/'control/PROJECT_MANIFEST.json',BUS/'control/MULTI_PROJECT_PROTOCOL_V3.md',BUS/'control/MESSAGE_ENVELOPE_SCHEMA.json',BUS/'control/DURABLE_COORDINATION_V1.md',BUS/'control/GITHUB_WRITE_SECURITY_POLICY.json',ROOT/'benefitflow_beta/coordination.py',ROOT/'benefitflow_beta/durable_store.py',ROOT/'benefitflow_beta/durable_coordination.py',ROOT/'benefitflow_beta/project_guard.py',ROOT/'tools/prove_multi_project_isolation.py')
CONTEXT=(BUS/'control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md',BUS/'control/ENHANCEMENT_SOURCE_REGISTRY.json',BUS/'control/ENHANCEMENT_CURSOR.json',ROOT/'SWARM_LAUNCH_KERNEL_V1.md',ROOT/'swarm_kernel/project.json',ROOT/'swarm_kernel/AGENT_BOOTSTRAP_OVERLAY.md',ROOT/'swarm_kernel/kernel.py')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def revision():
    try:return subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    except Exception:return 'UNAVAILABLE'
def expect(errors,label,actual,expected):
    if actual!=expected: errors.append(f'{label}: {actual!r} != {expected!r}')

def source_errors():
    e=[]
    for p in (*IDENTITY,*PROTOCOL_FILES,*CONTEXT):
        if not p.is_file(): e.append(f'missing required package context: {p.relative_to(ROOT)}')
    if e:return e
    lock=json.loads((BUS/'control/PROJECT_IDENTITY_LOCK.json').read_text())
    for k,v in {'project_id':'benefitflow','writable_repository':'boberino93-bit/benefitflow','canonical_branch':'main','coordination_root':'BenefitFlow-AgentBus/','mode':'FAIL_CLOSED','cross_project_write_policy':'DENY'}.items(): expect(e,f'identity lock {k}',lock.get(k),v)
    project=json.loads((BUS/'control/PROJECT_MANIFEST.json').read_text())
    required={'project_id':'benefitflow','repository_identity':'boberino93-bit/benefitflow','repository_id':REPO_ID,'protocol_version':PROTOCOL,'project_version':'alpha-0.4.2','package_version':'0.4.2-h3','cross_project_default':'DENY','cross_project_bridge':'EXPLICIT_COPY_BY_VALUE_ONLY','identity_mode':'FAIL_CLOSED','coordination_backend':'SQLITE_WAL_DURABLE_V1','audit_model':'APPEND_ONLY_SHA256_HASH_CHAIN','outbox_model':'APPEND_ONLY_EVENT_WITH_DELIVERY_RECEIPT','durable_project_control':True,'multi_process_proving_required':True}
    for k,v in required.items(): expect(e,f'project manifest {k}',project.get(k),v)
    binding=json.loads((BUS/'control/GITHUB_REPOSITORY_BINDING.json').read_text())
    expect(e,'repository binding name',binding.get('target_repository'),'boberino93-bit/benefitflow'); expect(e,'repository binding id',binding.get('target_repository_id'),REPO_ID)
    security=json.loads((BUS/'control/GITHUB_WRITE_SECURITY_POLICY.json').read_text())
    expect(e,'write-security repository',security.get('repository',{}).get('full_name'),'boberino93-bit/benefitflow'); expect(e,'write-security repository id',security.get('repository',{}).get('id'),REPO_ID); expect(e,'CI contents permission',security.get('ci',{}).get('token_permissions',{}).get('contents'),'read')
    root=json.loads((ROOT/'AGENT_BOOTSTRAP.json').read_text()); expect(e,'root bootstrap project',root.get('project_id'),'benefitflow'); expect(e,'root bootstrap repository id',root.get('repository',{}).get('id'),REPO_ID); expect(e,'project factory pointer',root.get('project_factory',{}).get('pointer'),'NEW_PROJECT_BOOTSTRAP.json')
    factory=json.loads((ROOT/'NEW_PROJECT_BOOTSTRAP.json').read_text()); expect(e,'new-project source project',factory.get('source_project',{}).get('project_id'),'benefitflow'); expect(e,'new-project no identity copy',factory.get('local_reference',{}).get('copy_identity_values'),False)
    schema=json.loads((BUS/'control/MESSAGE_ENVELOPE_SCHEMA.json').read_text()); expect(e,'message schema id',schema.get('$id'),'benefitflow/message-envelope/3.1.0')
    durable=(ROOT/'benefitflow_beta/durable_store.py').read_text()+'\n'+(ROOT/'benefitflow_beta/durable_coordination.py').read_text()
    for token in ('BEGIN IMMEDIATE','journal_mode=WAL','audit_log_no_update','outbox_no_update','class DurableCoordinationStore','verify_integrity','set_project_mode'):
        if token not in durable:e.append(f'durable runtime missing token: {token}')
    prover=(ROOT/'tools/prove_multi_project_isolation.py').read_text()
    for token in ('project-c','shared-idempotency-key','restart_idempotency_replay','benefitflow_safe_replays'):
        if token not in prover:e.append(f'proving harness missing token: {token}')
    for role in ROLES:
        p=BUS/'bootstrap'/f'{role}.md'; text=p.read_text() if p.is_file() else ''
        for token in ('RECENT CONTEXT IS NOT PROJECT AUTHORITY','PROJECT_IDENTITY_LOCK.json','3.1.0','MESSAGE_ENVELOPE_SCHEMA.json','DURABLE_COORDINATION_V1.md','DurableCoordinationStore','GITHUB_WRITE_SECURITY_POLICY.json','NEW_PROJECT_BOOTSTRAP.json'):
            if token not in text:e.append(f'{role} bootstrap missing token: {token}')
        if 'read-only' not in text.lower():e.append(f'{role} bootstrap missing foreign read-only boundary')
    gen=(ROOT/'tools/generate_successor_package.py').read_text()
    for token in ('benefitflow/successor-package/v8','NEW_PROJECT_BOOTSTRAP.json','durable_store.py','durable_coordination.py','DURABLE_COORDINATION_V1.md','GITHUB_WRITE_SECURITY_POLICY.json','prove_multi_project_isolation.py','multi_process_proving_required','SQLITE_WAL_DURABLE_V1'):
        if token not in gen:e.append(f'package generator missing token: {token}')
    return e

def verify_context(pkg,dirname,hashes,sources,e):
    d=pkg/dirname
    if not d.is_dir():e.append(f'package missing {dirname}');return
    for src in sources:
        p=d/src.name
        if not p.is_file():e.append(f'package missing {dirname}/{src.name}');continue
        rel=str(p.relative_to(pkg))
        if hashes.get(rel)!=sha(p):e.append(f'manifest checksum mismatch: {rel}')
        if sha(p)!=sha(src):e.append(f'package drift: {src.relative_to(ROOT)}')

def package_errors(pkg):
    e=[]; mp=pkg/'SUCCESSOR_MANIFEST.json'
    if not mp.is_file():return [f'missing successor manifest: {mp}']
    m=json.loads(mp.read_text()); project=json.loads((BUS/'control/PROJECT_MANIFEST.json').read_text())
    expected={'schema':PACKAGE_SCHEMA,'project_id':'benefitflow','repository_target':'boberino93-bit/benefitflow','repository_id':REPO_ID,'canonical_branch':'main','coordination_namespace':'BenefitFlow-AgentBus/','artifact_namespace':'BenefitFlow-AgentBus/artifactory/','identity_mode':'FAIL_CLOSED','foreign_source_mode':'READ_ONLY_FOREIGN_SOURCES','foreign_mutation_allowed':False,'cross_project_default':'DENY','cross_project_bridge':'EXPLICIT_COPY_BY_VALUE_ONLY','agent_lifecycle_binding_required':True,'child_project_inheritance_required':True,'task_artifact_project_ownership_required':True,'durable_coordination_required':True,'durable_coordination_contract':'PROTOCOL_CONTEXT/DURABLE_COORDINATION_V1.md','durable_coordination_runtime':'PROTOCOL_CONTEXT/durable_coordination.py','coordination_backend':'SQLITE_WAL_DURABLE_V1','audit_model':'APPEND_ONLY_SHA256_HASH_CHAIN','outbox_model':'APPEND_ONLY_EVENT_WITH_DELIVERY_RECEIPT','multi_process_proving_required':True,'multi_project_proving_harness':'PROTOCOL_CONTEXT/prove_multi_project_isolation.py','github_write_security_policy':'PROTOCOL_CONTEXT/GITHUB_WRITE_SECURITY_POLICY.json','new_project_factory_pointer':'IDENTITY_CONTEXT/NEW_PROJECT_BOOTSTRAP.json','project_version':project['project_version'],'protocol_version':project['protocol_version'],'package_version':project['package_version'],'swarm_kernel_version':'1.0.0','swarm_kernel_required':True}
    for k,v in expected.items():expect(e,f'package manifest {k}',m.get(k),v)
    live=revision()
    if not m.get('source_revision') or m.get('source_revision')=='UNAVAILABLE':e.append('package source_revision unavailable')
    elif live!='UNAVAILABLE' and m.get('source_revision')!=live:e.append(f'package source revision {m.get("source_revision")} != {live}')
    role=m.get('role')
    if role not in ROLES:e.append(f'unexpected package role: {role!r}')
    else:
        b=pkg/f'{role}_BOOTSTRAP.md'
        if not b.is_file():e.append(f'package missing {role}_BOOTSTRAP.md')
        elif m.get('bootstrap_sha256')!=sha(b):e.append(f'packaged {role} bootstrap checksum mismatch')
    verify_context(pkg,'IDENTITY_CONTEXT',m.get('identity_artifact_hashes',{}),IDENTITY,e); verify_context(pkg,'PROTOCOL_CONTEXT',m.get('protocol_artifact_hashes',{}),PROTOCOL_FILES,e)
    snap=pkg/'DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT'
    for src in (*IDENTITY,*PROTOCOL_FILES):
        p=snap/src.relative_to(ROOT)
        if not p.is_file():e.append(f'snapshot missing required artifact: {src.relative_to(ROOT)}')
    ctx=pkg/'ENHANCEMENT_CONTEXT'
    for src in CONTEXT:
        p=ctx/src.name
        if not p.is_file():e.append(f'package missing enhancement/kernel context: {src.name}')
        elif sha(p)!=sha(src):e.append(f'package enhancement/kernel drift: {src.relative_to(ROOT)}')
    return e

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package',action='append',default=[]); a=ap.parse_args(); e=source_errors()
    for p in a.package:e.extend(package_errors(Path(p)))
    if e:
        print(json.dumps({'valid':False,'errors':e},indent=2)); raise SystemExit(2)
    print(json.dumps({'valid':True,'roles':list(ROLES),'identity_mode':'FAIL_CLOSED','protocol_version':PROTOCOL,'repository_id':REPO_ID,'package_schema':PACKAGE_SCHEMA,'coordination_backend':'SQLITE_WAL_DURABLE_V1'},indent=2))
if __name__=='__main__':main()
