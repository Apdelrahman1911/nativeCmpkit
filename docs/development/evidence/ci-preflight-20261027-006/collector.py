from pathlib import Path
import datetime as dt, hashlib, json, os, re, subprocess, shutil, sys
ROOT=Path('/root/projects/nativeCmpKit'); BASE=ROOT/'build/ci-policy-tooling-20261027-006'; DEST=ROOT/'docs/development/evidence/ci-preflight-20261027-006'
DRIVER=Path('/tmp/nativecmpkit-preflight-20261027-006.py')
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests
assert not DEST.exists()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def current():
    names=subprocess.check_output(['git','--no-optional-locks','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    values={}
    for name in sorted(set(names)-{''}):
        p=ROOT/name
        if p.is_symlink(): values[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
        elif p.is_file(): values[name]={'kind':'regular','sha256':sha(p),'bytes':p.stat().st_size}
        elif not p.exists(): values[name]={'kind':'deleted'}
        else: raise ValueError('Nonregular input')
    return values
r=json.loads((BASE/'checks.json').read_bytes());before=json.loads((BASE/'inputs-before.json').read_bytes());after=json.loads((BASE/'inputs-after.json').read_bytes())
assert r['passed'] and r['source_revision']==r['source_revision_after']==library_tests.git_revision(ROOT)
assert r['commands_requested']==r['commands_completed']==21 and r['python_unittest_executions']==830
assert before==after==current() and not r['changed_inputs']
assert sha(DRIVER)==r['driver_sha256']
rows=[]
for item in r['results']:
    p=ROOT/item['log']; assert sha(p)==item['log_sha256'] and item['execution']['exit_code']==0 and not item['execution'].get('stop_reason')
    lines=p.read_text(errors='replace').splitlines()
    headers=[]
    for line in lines:
        m=re.match(r'^(test[A-Za-z0-9_]*) \(([A-Za-z0-9_.]+)\) \.\.\. (ok|ERROR|FAIL|expected failure|unexpected success)$',line)
        if m: headers.append({'method':m[1],'id':m[2],'outcome':m[3]})
    if item['unittest_count'] is not None:
        assert item['unittest_summary_ok'] and 'OK' in lines and len(headers)==item['unittest_count'] and all(h['outcome']=='ok' for h in headers)
    rows.append({'name':item['name'],'exit_code':0,'actual_tooling_methods':item['unittest_count'],'case_headers':headers,'log_sha256':sha(p),'summary_lines':[line for line in lines if re.match(r'^(Ran |OK$|FAILED|VALID:|CURRENT:|ERROR\s+-|WARNING\s+-|Aborted with )',line)]})
DEST.mkdir(parents=True)
for name in ['checks.json','inputs-before.json','inputs-after.json']:
    shutil.copyfile(BASE/name,DEST/name)
for item in r['results']: shutil.copyfile(ROOT/item['log'],DEST/Path(item['log']).name)
shutil.copyfile(DRIVER,DEST/'driver.py');shutil.copyfile('/tmp/nativecmpkit-actionlint-1.7.12/acquisition.json',DEST/'actionlint-acquisition.json')
(DEST/'lead-review.json').write_text(json.dumps({'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'base_revision':r['source_revision'],'dirty_snapshot':True,'all_held_inputs_unchanged_during_check_and_before_archive':True,'source_input_count':len(before),'commands_exit_zero':21,'python_tooling_methods_passed':830,'ci_methods_passed':150,'reviewed_commands':rows,'library_native_packaged_consumer_methods_executed':0,'publication_performed':False,'release_gate_cleared':False,'limitations':['This archive and later documentation edits are additive after the held snapshot; this is not circular self-verification.','Actionlint and Python fixtures do not execute Android, UIKit or Windows ACL/reparse behavior.','Exact documentation dependency version/digest observations do not certify independent dependency trust.']},indent=2,sort_keys=True)+'\n')
shutil.copyfile(Path(__file__),DEST/'collector.py')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file()))
print(json.dumps({'archive':str(DEST.relative_to(ROOT)),'source_inputs':len(before),'python_methods':830,'commands':21},indent=2))
