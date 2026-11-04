#!/usr/bin/env python3
"""Independent passive qualification; candidate modules and tests are never imported."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import json
import stat

O=Path(__file__).resolve().parent
P=Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-report-custody-successor658')
B=Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
def data(path):
    path=Path(path);a=path.stat(follow_symlinks=False)
    assert stat.S_ISREG(a.st_mode) and not path.is_symlink() and a.st_nlink==1
    b=path.read_bytes();z=path.stat(follow_symlinks=False)
    assert tuple(getattr(a,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode'))==tuple(getattr(z,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode'))
    return b

def sha(b):return hashlib.sha256(b).hexdigest()
def pin(path):
    b=data(path);return {'path':str(path),'bytes':len(b),'sha256':sha(b)}
def matched(path,row):
    b=data(path);assert len(b)==row['bytes'] and sha(b)==row['sha256'];return b

def functions(tree):
    result={}
    for n in tree.body:
        if isinstance(n,ast.FunctionDef):result[n.name]=n
        if isinstance(n,ast.ClassDef):
            for f in n.body:
                if isinstance(f,ast.FunctionDef):result[n.name+'.'+f.name]=f
    return result

def ash(n):return sha(ast.dump(n,include_attributes=False).encode())
def fullname(n):
    if isinstance(n,ast.Name):return n.id
    if isinstance(n,ast.Attribute):return fullname(n.value)+'.'+n.attr
    return ''
def calls(tree,name):return sorted((n for n in ast.walk(tree) if isinstance(n,ast.Call) and fullname(n.func)==name),key=lambda n:n.lineno)

recipe=json.loads(data(P/'EXACT-REPORT-CUSTODY-CORRECTION658.json'))
assert pin(P/'EXACT-REPORT-CUSTODY-CORRECTION658.json')['sha256']=='498af0e70ba061e178abdf325970bfaa568d73679fecac9fa97ecc8012d65746'
matched(recipe['independent705_refusal']['path'],recipe['independent705_refusal'])
assert pin(B/'PACKET-SEAL658.json')['sha256']=='52b7415a32687bc4dc9838057cca8ab3dee45e11c2dc43cead1b5ad80bd3df34'
base=json.loads(data(O/'PASSIVE-BASE-SOURCE-RESULTS705.json'))
assert pin(O/'PASSIVE-BASE-SOURCE-RESULTS705.json')['sha256']=='a7ed7fd5692b8f1f7052e91d0b076319f55141a0c7bbc04e4574cdc09c8195d3'
scopes={};new_source_pins={}
for key,name in [('driver','javafx_ordinary_maven_consumer.py'),('source_controls','test_javafx_ordinary_maven_route.py')]:
    r=recipe[key];old=matched(B/'proposed/scripts/ci'/name,r['before']);new=matched(P/'proposed/scripts/ci'/name,r['after'])
    forward=old
    for f in r['fragments']:
        a,b=f['preimage'].encode(),f['postimage'].encode()
        assert f['kind']=='replace-exact-once' and forward.count(a)==1
        forward=forward.replace(a,b,1)
    assert forward==new
    inverse=new
    for f in reversed(r['fragments']):
        a,b=f['preimage'].encode(),f['postimage'].encode();assert inverse.count(b)==1;inverse=inverse.replace(b,a,1)
    assert inverse==old
    of,nf=functions(ast.parse(old)),functions(ast.parse(new))
    changed=sorted(k for k in of if ash(of[k])!=ash(nf[k]));added=sorted(set(nf)-set(of));assert not(set(of)-set(nf))
    if key=='driver':
        assert changed==['fresh_resolution','run'] and added==['resolution_report_held','retained_resolution']
        assert {k:ash(v) for k,v in of.items()}==r['old_function_ASTs'] and {k:ash(v) for k,v in nf.items()}==r['new_function_ASTs']
        driver=nf;driver_source=new.decode()
    else:
        assert changed==['JavafxOrdinaryMavenRouteSourceTests.test_both_complete_graphs_bind_before_single_new_native_request']
        assert sorted(added)==sorted(r['NEW_methods'])
        assert {k:ash(v) for k,v in of.items()}==r['old_function_and_method_ASTs'] and {k:ash(v) for k,v in nf.items()}==r['new_function_and_method_ASTs']
        imports=[n for n in ast.parse(new).body if isinstance(n,(ast.Import,ast.ImportFrom))]
        modules={n.module if isinstance(n,ast.ImportFrom) else a.name for n in imports for a in ([None] if isinstance(n,ast.ImportFrom) else n.names)}
        assert modules=={'__future__','ast','hashlib','json','pathlib','re','stat','unittest'}
        assert not any(calls(ast.parse(new),bad) for bad in ('eval','exec','compile','__import__','subprocess.run','os.system','runpy.run_path'))
    scopes[key]={'exact_forward_inverse_fragments':len(r['fragments']),'only_existing_changed':changed,'only_NEW':added,'all_other_named_ASTs_held':True}
    new_source_pins[name]=pin(P/'proposed/scripts/ci'/name)

# Inspect exact material data flow without evaluating candidate functions.
capture=driver['retained_resolution'];guard=driver['resolution_report_held'];fresh=driver['fresh_resolution'];run=driver['run']
assert len(calls(capture,'read'))==1 and ast.unparse(calls(capture,'read')[0].args[0])=='path'
assert len(calls(capture,'json.loads'))==1 and ast.unparse(calls(capture,'json.loads')[0].args[0])=='payload'
assert {k.arg:ast.unparse(k.value) for k in calls(capture,'json.loads')[0].keywords}=={'object_pairs_hook':'unique','parse_constant':'finite'}
assert calls(capture,'saved.open')[0].args[0].value=='xb' and ast.unparse(calls(capture,'stream.write')[0].args[0])=='payload'
assert calls(capture,'stream.write')[0].lineno<calls(capture,'stream.flush')[0].lineno<calls(capture,'os.fstat')[0].lineno
assert not calls(capture,'packaged.read_json') and not calls(fresh,'packaged.read_json')
assert ast.unparse(calls(fresh,'invoke')[0].args[1].elts[-1])=="custody['path']"
assert calls(fresh,'bound_resolution')[0].lineno<calls(fresh,'resolution_report_held')[0].lineno<next(n.lineno for n in fresh.body if isinstance(n,ast.Return))
post=next(n for n in calls(run,'invoke') if n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='post-native-production-pin-graph-binding')
assert ast.unparse(post.args[1].elts[-1])=="native_custody['path']"
post_guard=next(n for n in calls(run,'resolution_report_held') if ast.unparse(n.args[0])=='native_custody')
post_graph=next(n for n in calls(run,'graph_signature') if ast.unparse(n.args[0])=='current')
assert post.lineno<post_guard.lineno<post_graph.lineno
assert calls(run,'resolution_reports.append') and "record['resolution_reports_held'] = False" in driver_source
assert "held.append(record['resolution_reports_held'])" in driver_source and "record['passed'] = record['passed'] and bool(held) and all(held)" in driver_source
for bad in ('path.unlink','path.write_bytes','path.write_text','path.rename','os.remove','os.replace'):assert not calls(guard,bad)

original_recipe=json.loads(data(B/'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json'))
assert recipe['unchanged_exact12_donor_sources']=={k:v for k,v in original_recipe['source_files'].items() if k in recipe['unchanged_exact12_donor_sources']}
assert len(recipe['unchanged_exact12_donor_sources'])==12
for name,row in recipe['unchanged_workflow_and_doc'].items():
    assert matched(P/'proposed'/name,row)==matched(B/'proposed'/name,row)
    new_source_pins[name]=pin(P/'proposed'/name)

value={
 'schema':'nativecmpkit-independent705-windows658-retained-report-preexecution-source-qualification-v1','utc':datetime.now(timezone.utc).isoformat(),
 'decision':'Exact NEW-driver retained-report correction qualifies for the separately authorized changed1+NEW2 passive AST/text source selection. Source-only pre-execution qualification, not test results, adoption or actual Windows/native acceptance.',
 'correction_recipe':pin(P/'EXACT-REPORT-CUSTODY-CORRECTION658.json'),'base_review_reused':pin(O/'PASSIVE-BASE-SOURCE-RESULTS705.json'),'original_refusal_retained':pin(O/'REPORT-BYTE-CUSTODY-REFUSAL705.json'),'location_addendum':pin(O/'LOCATION-ONLY-CORRECTION705.json'),
 'source_files':new_source_pins,'exact_composition':scopes,
 'confirmed_gap_source_addressed':{'same_raw_capture_saved_and_parsed':True,'strict_duplicate_nonfinite_object_parse':True,'retained_paths_only_to_unchanged_production_verifier':True,'freshness_binds_same_original_identity':True,'post_verifier_custody_before_graph_and_native_reuse':True,'complete_mode_reports_held_before_native':True,'final_report_custody_gates_passed':True,'retained_evidence_never_deleted_or_rewritten':True},
 'qualified_only_selection':recipe['source_controls']['only_selected_methods'],'qualified_only_method_count':3,
 'unchanged_reused_not_replayed':{'existing_route_methods':9,'workflow_and_doc':True,'all12_donor_sources':True,'original_Actionlint_and_failed_only_recovery':True,'old_library_Stop_control_native_or_consumer_populations':True},
 'platform_risks_not_confirmed_failures':[{'location':'retained_resolution:166-173','risk':'Stored timestamps come from fstat before the retained writer handle closes; Windows may finalize write metadata on close. No Windows timestamp behavior was executed here. The current strict guard fails closed on any difference, never silently accepts another graph.','recommendation':'Guarded closed-file timestamp baseline with dev/ino tied to the owned descriptor, or actual Windows capture/identity regression evidence before native acceptance.'}],
 'source_preparation_refusal_retained':pin(P/'PREPARATION-EXACT-PATH-FRAGMENT-REFUSAL658.json'),
 'nonexecutions':{'candidate_imports_source_controls_or_lint':0,'tests_build_stage_native':0,'Git_GitHub_network':0,'ROOT_or_target_edits':0,'delegation':0,'closure_publication':0},
 'remaining':'Lead controls exact audited execution-plan/input-map gate, original result review, successor16-source recipe, independent/lead source-only adoption, target HEAD/cleanliness/modes/preimages/15absences, full-checkout compiler/native, producer/Camera/Android cohort and hosted capacity. No native/security/consumer/API-ABI/legal/dependency/readiness/publication/issue clearance.'}
f=O/'SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json'
with f.open('x',encoding='utf-8') as out:json.dump(value,out,indent=2,sort_keys=True);out.write('\n')
f.chmod(0o600)
print(json.dumps(pin(f),sort_keys=True))
