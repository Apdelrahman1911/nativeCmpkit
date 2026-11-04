#!/usr/bin/env python3
"""Reviewer705 passive exact source/result/target readback. No target imports/tests/Git."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import json
import stat

P = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
O = Path(__file__).resolve().parent
T = Path('/root/nativecmpkit-worktrees/javafx-ordinary-consumer1')
H = hashlib.sha256

def digest(raw): return H(raw).hexdigest()
def raw(path):
    path=Path(path); before=path.stat(follow_symlinks=False)
    assert stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1
    b=path.read_bytes(); after=path.stat(follow_symlinks=False)
    keys=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode')
    assert tuple(getattr(before,k) for k in keys)==tuple(getattr(after,k) for k in keys)
    return b

def document(path): return json.loads(raw(path))
def pin(path):
    path=Path(path); b=raw(path)
    return {'path':str(path),'bytes':len(b),'sha256':digest(b)}
def match(path,row):
    b=raw(path); assert len(b)==row['bytes'] and digest(b)==row['sha256'];return b

def write(name,value):
    path=O/name
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    path.chmod(0o600);return pin(path)

utc=lambda:datetime.now(timezone.utc).isoformat()
recipe=document(P/'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json')
small=document(P/'FINAL16-SOURCE-RESULTS-SEAL658.json')
seal=document(P/'PACKET-SEAL658.json')
assert pin(P/'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json')['sha256']=='adf80ea4a7ae3aa0d4acad299b8efe4ffd2444aca6a797694a2689b363072b32'
assert pin(P/'FINAL16-SOURCE-RESULTS-SEAL658.json')['sha256']=='cc99fdb35d9b104aff162c85d3b576698b504b4deb773d1789437b72bf71c87f'
assert pin(P/'PACKET-SEAL658.json')['sha256']=='52b7415a32687bc4dc9838057cca8ab3dee45e11c2dc43cead1b5ad80bd3df34'
actual_files=sorted(q.relative_to(P).as_posix() for q in P.rglob('*') if q.is_file() and q.name!='PACKET-SEAL658.json')
assert actual_files==sorted(seal['files']) and len(actual_files)==80
for name,row in seal['files'].items():
    match(P/name,row);assert f'{stat.S_IMODE((P/name).stat().st_mode):04o}'==row['external_mode']
assert sum(row['bytes'] for row in seal['files'].values())==seal['file_bytes']==1168578

original=document(recipe['original_exact12_authority']['path'])
match(recipe['original_exact12_authority']['path'],recipe['original_exact12_authority'])
source_rows={}
for name,row in recipe['source_files'].items():
    match(row['source_path'],row);assert f'{stat.S_IMODE(Path(row["source_path"]).stat().st_mode):04o}'==row['source_mode_observed']
    sr=small['source_files'][name]
    assert all(sr[k]==row[k] for k in ('bytes','sha256','source_path','root_preimage','expected_mode','expected_git_mode'))
    if name in original['source_files']:
        old=original['source_files'][name]
        assert old['sha256']==row['sha256'] and old['bytes']==row['bytes'] and old['source_path']==row['source_path']
    source_rows[name]={k:row[k] for k in ('bytes','sha256','expected_mode','expected_git_mode')}
assert len(source_rows)==16 and sum(x['bytes'] for x in source_rows.values())==232222
assert len(original['source_files'])==12 and sum(x['bytes'] for x in original['source_files'].values())==161381

cached=Path(recipe['cached_independent620_authority']['path'])
match(cached,recipe['cached_independent620_authority'])
cs=document(cached)
# The named cached acceptance is reused; no historical test/cohort replay.
for row in cs['files']:match(cached.parent/row['path'],row)
cr=document(cached.parent/'REVIEW.json')
assert not cr['errors'] and len(cr['derivatives'])==5 and sum(x['fragments'] for x in cr['derivatives'])==33

wd=recipe['workflow_derivative'];pre=raw(P/'retained/javafx-library-candidate.preimage.yml');post=raw(recipe['source_files'][wd['destination']]['source_path'])
assert digest(pre)==wd['preimage']['sha256'] and digest(post)==wd['postimage']['sha256']
forward=pre
for fragment in wd['fragments']:
    a,b=fragment['preimage'].encode(),fragment['postimage'].encode()
    if fragment['kind']=='replace-exact-once':
        assert forward.count(a)==1;forward=forward.replace(a,b,1)
    else:
        assert fragment['kind']=='append-at-exact-predecessor-EOF' and a==b'';forward+=b
assert forward==post
inverse=post
for fragment in reversed(wd['fragments']):
    a,b=fragment['preimage'].encode(),fragment['postimage'].encode()
    if fragment['kind']=='append-at-exact-predecessor-EOF':assert inverse.endswith(b);inverse=inverse[:-len(b)]
    else:assert inverse.count(b)==1;inverse=inverse.replace(b,a,1)
assert inverse==pre
oldjob=pre[pre.index(b'  public-stop:\n'):]
assert len(oldjob)==wd['complete_old_public_stop_job']['bytes']==7294 and digest(oldjob)==wd['complete_old_public_stop_job']['sha256']
assert oldjob in post and b'contents: read\n' in pre

correction=document(P/'CORRECTION-FAILED-AND-CHANGED2-RECIPE658.json')
original_controls=raw(P/correction['original_source_controls']['retained_path'])
controls=raw(recipe['source_files']['scripts/ci/test_javafx_ordinary_maven_route.py']['source_path'])
candidate=original_controls
for f in correction['control_fragments']:
    a,b=f['preimage'].encode(),f['postimage'].encode();assert candidate.count(a)==1;candidate=candidate.replace(a,b,1)
assert candidate==controls
oldtree=ast.parse(original_controls);newtree=ast.parse(controls)
def methods(tree):
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='JavafxOrdinaryMavenRouteSourceTests')
    return {n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
oldmethods,newmethods=methods(oldtree),methods(newtree)
changed=[name for name in oldmethods if ast.dump(oldmethods[name],include_attributes=False)!=ast.dump(newmethods[name],include_attributes=False)]
assert set(changed)=={'test_final_custody_and_material_gates_keep_missing_scope_unqualified','test_new_job_is_separate_manual_windows_and_read_only'}
unchanged=[name for name in oldmethods if name.startswith('test_') and name not in changed];assert len(unchanged)==8

results={}
first_saved={str(P/'proposed/.github/workflows/javafx-library-candidate.yml'):P/'retained/javafx-library-candidate.before-actionlint-recovery658.yml',str(P/'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'):P/'retained/test_javafx_ordinary_maven_route.before-failed-fixture-recovery658.py'}
for label,reference in small['actual_results'].items():
    b=match(P/reference['path'],reference);d=json.loads(b);before=document(P/label/'source-inputs-before.json');after=document(P/label/'source-inputs-after.json')
    assert before==after and d['source_inputs_held'] and len(before['files'])==d['actual_named_input_count'] and len(before['ROOT_destinations_absent'])==17 and all(before['ROOT_destinations_absent'].values())
    qualifiers=document(P/('QUALIFIED-SOURCE-INPUTS658.json' if label.startswith('FIRST-') else 'QUALIFIED-RECOVERY-SOURCE-INPUTS658.json'))
    assert before['files']=={name:{k:row[k] for k in ('bytes','sha256')} for name,row in qualifiers['inputs'].items()}
    assert d['qualification_map_sha256']==pin(P/('QUALIFIED-SOURCE-INPUTS658.json' if label.startswith('FIRST-') else 'QUALIFIED-RECOVERY-SOURCE-INPUTS658.json'))['sha256']
    assert d['plan_sha256']==pin(P/('NEW-ROUTE-EXECUTION-PLAN658.json' if label.startswith('FIRST-') else 'ONLYFAILED-CHANGED2-RECOVERY-EXECUTION-PLAN658.json'))['sha256']
    for name,row in before['files'].items():match(first_saved.get(name,Path(name)) if label.startswith('FIRST-') else Path(name),row)
    for name,row in d['streams'].items():match(P/label/name,row)
    if 'audit' in d:assert document(P/label/'audit.json')==d['audit'] and not d['audit']['denied_attempts']
    results[label]={'result':pin(P/label/'result.json'),'exit_code':d['exit_code'],'outer_seconds':d['elapsed_seconds'],'named_inputs':d['actual_named_input_count'],'before_after_held':True,'historic_preimage_substitutions':2 if label.startswith('FIRST-') else 0,'methods':d.get('selected_NEW_methods',[])}

helperq=document(P/'NAMED-LIBRARY-HELPER-QUALIFICATION658.json')
historical=raw(helperq['exact_historical_predecessor']['path']);current=raw(T/'scripts/ci/library_tests.py')
match(helperq['exact_historical_predecessor']['path'],helperq['exact_historical_predecessor'])
hast,cast=ast.parse(historical),ast.parse(current)
def funcs(tree):return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
hf,cf=funcs(hast),funcs(cast)
helpers={}
for name,row in helperq['consumed_unchanged_helper_API_ASTs'].items():
    a=ast.dump(hf[name],include_attributes=False);b=ast.dump(cf[name],include_attributes=False)
    assert a==b and digest(a.encode())==row['AST_sha256'];helpers[name]=row['AST_sha256']
def without(raw_bytes,tree):
    lines=raw_bytes.decode().splitlines(keepends=True)
    scopes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('run','main')]
    for n in sorted(scopes,key=lambda n:n.lineno,reverse=True):del lines[n.lineno-1:n.end_lineno]
    return ''.join(lines)
assert without(historical,hast)==without(current,cast)
refs=document(P/'CURRENT-BOUNDED-ROUTE-REFERENCES658.json');boundrefs=[];sparse_missing=[]
for name,row in refs['references'].items():
    if name=='scripts/ci/library_tests.py':continue
    if not (T/name).exists():
        assert not (T/name).is_symlink();sparse_missing.append(name);continue
    match(T/name,row);boundrefs.append(name)

mode_receipt=Path('/root/nativecmpkit-source-proposals-20261104/lead-javafx-ordinary-integration710/MODE-ONLY-CORRECTION-READBACK710.json')
target=T/wd['destination'];tb=raw(target);ts=target.stat(follow_symlinks=False)
assert tb==pre and stat.S_IMODE(ts.st_mode)==0o644
absent={name:not(T/name).exists() and not(T/name).is_symlink() for name,row in recipe['source_files'].items() if row['root_preimage'] is None}
assert len(absent)==15 and all(absent.values())
assert not(T/'gradle/verification-metadata.xml').exists() and not(T/'gradle/verification-metadata.xml').is_symlink()

base={
 'schema':'nativecmpkit-independent705-windows658-frozen-base-source-results-v1','reviewer':'/root/producer_budget_review705','utc':utc(),
 'decision':'Frozen original source/results custody and composition qualify; adoption withheld for confirmed NEW-driver consumed-report custody gap. No source, test or native execution.',
 'packet_seal':pin(P/'PACKET-SEAL658.json'),'small_seal':pin(P/'FINAL16-SOURCE-RESULTS-SEAL658.json'),'recipe':pin(P/'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json'),
 'packet':{'files':80,'bytes':1168578,'actual_hashes_sizes_and_external_modes_held':True},
 'sources':source_rows,'exact_sources':{'count':16,'bytes':232222,'unchanged_donors':12,'unchanged_donor_bytes':161381,'route_files':4,'route_bytes':70841},
 'workflow':{'fragments':2,'whole_forward_inverse':True,'old_job_bytes':7294,'old_job_sha256':digest(oldjob),'old_triggers_defaults_guards_permissions_concurrency_whitelist_held':True,'all_NEW_files':15},
 'results':results,'chronology':'FIRST10 remains9pass/1fail; onlyfailed formatter1+changed NEW-job1 passes2/2 once. Initial Actionlint1 preserves unsupported NEW verify-signature diagnostic; onlyfailed Actionlint0. Eight unchanged passes reused, not fresh10 green.',
 'recovery':{'control_fragments':3,'only_two_changed_method_ASTs':changed,'eight_unchanged_method_ASTs':unchanged,'controller_and_doc_unchanged':True},
 'cached620':{'seal':pin(cached),'33_inverse_forward_spans_reused_not_rechecked_or_executed':True,'old_control_and_native_populations_replayed':False,'source_only_limits_preserved':True},
 'named_helper_qualification':{'eleven_consumed_ASTs':helpers,'outside_run_and_main_bytes_identical':True,'other_named_references_held_at_target':boundrefs,'sparse_missing_runtime_prerequisites_not_adoption_overwrites':sparse_missing,'EvidenceError_is_ValueError':True,'routine_command_report_interfaces_source_compatible':True,'actual_native_or_controller_execution':False},
 'target':{'worktree':str(T),'branch_and_HEAD_authority':'Lead report only; no independent Git query','lead_reported_HEAD':'086224e97cf74c1cc30277b4c6b321867de725df','workflow_preimage':pin(target),'mode':f'{stat.S_IMODE(ts.st_mode):04o}','device':ts.st_dev,'inode':ts.st_ino,'nlink':ts.st_nlink,'NEW_absences':absent,'git_mode':'100644 expectation; lead must verify at adoption','first_independent_mode0600_observation':'Read-only tool output before correction; no independent prior inode attribution','lead_mode_only_correction_receipt':pin(mode_receipt),'gradle_verification_metadata_present':False},
 'nonexecutions':{'target_imports':0,'tests_lint_build_stage_native':0,'Git_GitHub_network':0,'ROOT_or_target_writes':0,'delegation':0,'publication_or_closure':0},
 'reviewer_refusals_retained':[pin(O/'FIRST-PASSIVE-REVIEWER-SCHEMA-REFUSAL705.json'),pin(O/'SECOND-PASSIVE-REVIEWER-SPARSE-SCOPE-REFUSAL705.json')],
 'next':'658 minimal external NEW-driver/control successor only; retain this original/refusal. Lead rechecks HEAD/cleanliness/preimages/modes/15 absences at eventual adoption. Compiler/native/real graph/hosted-dispatch/security/legal/consumer/API-ABI/issue/release gates remain.'}
bpin=write('PASSIVE-BASE-SOURCE-RESULTS705.json',base)
rpin=pin(O/'REPORT-BYTE-CUSTODY-REFUSAL705.json')
print(json.dumps({'base_review':bpin,'source_refusal':rpin,'target_actual_mode':'0644','target_absences':15,'source_adoption_accepted':False},sort_keys=True))
