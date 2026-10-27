from pathlib import Path
import datetime as dt, hashlib, json, re, shutil, sys, subprocess
ROOT=Path('/root/projects/nativeCmpKit')
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as lib

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,obj):
 with path.open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def sums(dest):
 (dest/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(dest).as_posix()}\n' for p in sorted(dest.rglob('*')) if p.is_file()))

DEST=ROOT/'docs/development/evidence/android-utp-xml-contract-20261027'; assert not DEST.exists()
rows=[];held={}
for number,name,expected,tests,fails in [('001','red',1,20,2),('002','green',0,146,0)]:
 src=ROOT/f'build/android-utp-xml-contract-20261027-{number}'
 r=json.loads((src/'receipt.json').read_bytes());before=json.loads((src/'inputs-before.json').read_bytes());after=json.loads((src/'inputs-after.json').read_bytes())
 assert before==after and len(before)==r['selected_inputs']==704 and r['exit_code']==expected
 log=src/(name+'.log');assert sha(log)==r['log_sha256']
 txt=log.read_text();headers=re.findall(r'^(test\w*) \(([^\n()]+)\) \.\.\. (ok|FAIL|ERROR)$',txt,re.M)
 assert len(headers)==tests and sum(h[2]=='FAIL' for h in headers)==fails and all(h[2]!='ERROR' for h in headers)
 assert re.search(rf'^Ran {tests} tests in ',txt,re.M)
 assert ('\nOK\n' in txt)==(expected==0)
 if name=='green':assert before==lib.snapshot_inputs(ROOT)
 held[name]=before
 rows.append({'name':name,'fixture_methods_executed':tests,'passing_methods':tests-fails,'failing_methods':fails,'exit_code':expected,'source_input_count':len(before),'inputs_unchanged_during_execution':True,'log_sha256':sha(log),'case_headers':[{'method':a,'id':b,'outcome':c} for a,b,c in headers]})
DEST.mkdir(parents=True)
for number,name in [('001','red'),('002','green')]:
 src=ROOT/f'build/android-utp-xml-contract-20261027-{number}';target=DEST/name;target.mkdir()
 for filename in ['receipt.json','inputs-before.json','inputs-after.json',name+'.log']:shutil.copyfile(src/filename,target/filename)
changes=[{'path':p,'red_sha256':held['red'].get(p),'green_sha256':held['green'].get(p)} for p in sorted(set(held['red'])|set(held['green'])) if held['red'].get(p)!=held['green'].get(p)]
for path in ['scripts/ci/library_tests.py','scripts/ci/fresh-tests.init.gradle.kts','scripts/ci/test_android_verification_contract.py']:
 assert sha(ROOT/path)==held['green'][path]
 target=DEST/'source'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
put(DEST/'lead-independent-review.json',{'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'base_revision':lib.git_revision(ROOT),'dirty_worktree_diagnostic':True,'reviewed_runs':rows,'selected_input_deltas':changes,'green_held_inputs_unchanged_before_archive':True,'library_or_android_methods_executed':0,'scope':'Synthetic source-bound Android report collector regressions. Red reproduces the directory contract mismatch; green preserves strict source-defined collection and rejects protobuf/intermediate substitution. Actual run40434024680 supplies the separate observed UTP location, not testcase outcomes. These counts overlap with the forthcoming full preflight, not independent library tests.','limitations':['Red source hashes are held but all historical red bytes are not copied/reconstructed here. Green source bytes are captured unchanged before archive.','No Android device is launched by this diagnostic. No native testcase count is inferred from filenames/hashes.'],'release_readiness_certified':False,'issues_closed':0})
shutil.copyfile(Path(__file__),DEST/'collector.py');sums(DEST)

DEST=ROOT/'docs/development/evidence/uikit-application-bindings-20261027';assert not DEST.exists()
rows=[]
for number,code in [('001',1),('002',0)]:
 src=ROOT/f'build/uikit-application-bindings-20261027-{number}'
 r=json.loads((src/'receipt.json').read_bytes());before=json.loads((src/'inputs-before.json').read_bytes());after=json.loads((src/'inputs-after.json').read_bytes())
 assert before==after and r['input_bytes_unchanged'] and r['execution']['exit_code']==code and r['source_revision']==lib.git_revision(ROOT)
 assert sha(src/'compile.log')==r['compile_log_sha256']
 assert all(Path(p).is_file() and sha(Path(p))==h for p,h in before.items())
 assert not r['apple_linking_performed'] and r['ios_runtime_methods_executed']==r['library_methods_executed']==0
 rows.append({'attempt':number,'compile_exit_code':code,'held_inputs_unchanged_at_execution_and_before_archive':True,'input_count':len(before),'output_digest_observed_at_execution':r['output_sha256'],'output_bytes_observed_at_execution':r['output_bytes'],'output_retained_for_independent_archive_check':False,'errors':src.joinpath('compile.log').read_text().splitlines() if code else [],'zero_apple_or_library_runtime_methods':True})
DEST.mkdir(parents=True)
for number in ['001','002']:
 src=ROOT/f'build/uikit-application-bindings-20261027-{number}';target=DEST/number;target.mkdir()
 for name in ['receipt.json','inputs-before.json','inputs-after.json','driver.py','compile.log','UIKitApplicationProbe.kt']:shutil.copyfile(src/name,target/name)
put(DEST/'lead-independent-review.json',{'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision_at_execution':lib.git_revision(ROOT),'reviewed_runs':rows,'scope':'Actual Kotlin/Native2.4.20 iOS-simulator KLIB lowering on Linux only. Preserves invalid internal ObjC-class access/final delegate property/enum import failure then the public runtime-name/owned-window correction. No application executable, Apple linking, UIKit launch, native hosting or library test behavior is certified.','ios_runtime_methods_executed':0,'library_methods_executed':0,'release_readiness_certified':False,'limitations':['Owned tmpfs KLIB output was deleted by its diagnostic driver; the output digest is a recorded observation, not independently rehashed archive bytes.','This is an unintegrated diagnostic source, not an active library/test application host.','Successful lowering does not verify ObjC registration, UIApplication lifecycle, worker scheduling or exit behavior on Apple.']})
shutil.copyfile(Path(__file__),DEST/'collector.py');sums(DEST)
print(json.dumps({'archives_created':['docs/development/evidence/android-utp-xml-contract-20261027','docs/development/evidence/uikit-application-bindings-20261027'],'library_methods_executed':0}))
