"""Read-only original UI-009 acceptance; no execution or GitHub mutation."""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = '6eb7c66eb01b390353100c63882cd102846c7b8d'
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

sha = lambda p: hashlib.sha256(p if isinstance(p, bytes) else p.read_bytes()).hexdigest()

def document(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))

finding = next(x for x in document((ROOT/'docs/audit/findings/UI.json').read_bytes()) if x['id']=='UI-009')
ledger_path = next(p for p in (ROOT/'docs/development/resolutions').glob('*.json')
                   if any(x['id']=='UI-009' for x in document(p.read_bytes())))
ledger = next(x for x in document(ledger_path.read_bytes()) if x['id']=='UI-009')
issue = document((OUT/'issue-123-before.json').read_bytes())
assert issue['repository_url']==f'https://api.github.com/repos/{REPO}' and issue['state']=='open'
assert issue['body'].startswith('<!-- nativecmpkit-item:audit:UI-009 -->')
assert all(x in issue['body'] for x in finding['required_tests'])
assert len(finding['required_tests'])==2

records = {}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
    if row:
        meta,name=row.split(b'\t',1)
        records[name.decode()]=meta.decode().split()
cache = {}
def git_hashes(names):
    needed = [name for name in names if name not in cache]
    if needed:
        assert all(records[n][0] in ('100644','100755') and records[n][1]=='blob' for n in needed)
        oids = [records[n][2] for n in needed]
        payload = subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,
                     input=''.join(oid+'\n' for oid in oids).encode())
        offset = 0
        for name,oid in zip(needed,oids):
            end=payload.index(b'\n',offset);head=payload[offset:end].split()
            assert head[0].decode()==oid and head[1]==b'blob'
            size=int(head[2]);offset=end+1;data=payload[offset:offset+size]
            assert len(data)==size and payload[offset+size:offset+size+1]==b'\n'
            offset+=size+1;cache[name]=sha(data)
        assert offset==len(payload)
    return {name:cache[name] for name in names}

paths = [
    'calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.kt',
    'calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.material.kt',
    'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.ios.kt',
    'calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerStateContractTest.kt',
    'calf-ui/build.gradle.kts',
]
# Same exact owning state/model/test/build files, not merely equal method names.
current = {name:sha(ROOT/name) for name in paths}
assert current==git_hashes(paths)
for name in paths[1:3]:
    source=(ROOT/name).read_text()
    assert 'require(initialHour in 0..23)' in source and 'require(initialMinute in 0..59)' in source
test_source=(ROOT/paths[3]).read_text()
for token in ('listOf(-1, 24)','listOf(-1, 60)','listOf(0, 23)','listOf(0, 59)',
              'saver.restore(listOf(0, 60, true))','assertEquals(59, restored.minute)',
              'assertEquals(23, restored.hour)','assertTrue(restored.is24hour)'):
    assert token in test_source

expected = {'rejectsInvalidHoursAndMinutes','acceptsBoundaryValues','saverRoundTripAndCorruptedInputValidation'}
scopes = []
for run,art,slot in [
    (40414284598,12695176692,'desktop-linux-x64'),
    (40414284598,12694901836,'android-host'),
    (40415332643,12695871736,'desktop-macos-arm64'),
    (40415332643,12695299854,'ios-iphone'),
]:
    base=ROOT/'docs/development/evidence/github-actions'/str(run)
    rv=document((base/'run-final.json').read_bytes())
    assert rv['id']==run and rv['repository']['full_name']==REPO and rv['head_sha']==REV
    assert rv['status']=='completed' and rv['run_attempt']==1 and rv['event']=='workflow_dispatch'
    arts=document((base/'artifacts-final.json').read_bytes())['artifacts']
    a=next(x for x in arts if x['id']==art)
    raw=base/'raw'/f'{art}.zip'
    assert raw.stat().st_size==a['size_in_bytes'] and 'sha256:'+sha(raw)==a['digest']
    assert a['workflow_run']['id']==run and a['workflow_run']['head_sha']==REV
    with zipfile.ZipFile(raw) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        assert len(names)==len(set(names)) and len(names)<2000
        assert sum(i.file_size for i in infos)<lt.MAX_TOTAL_REPORT_BYTES
        for i in infos:
            path=PurePosixPath(i.filename)
            assert not path.is_absolute() and not {'.','..'}&set(path.parts) and '\\' not in i.filename
            assert not i.is_dir() and not i.flag_bits&1 and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
            assert i.filename.endswith(('.xml','.json')) and i.file_size<=lt.MAX_REPORT_BYTES
        prefix=f'build/ci-verification/{slot}/'
        receipt=document(z.read(prefix+'receipt.json'))
        before=document(z.read(prefix+'inputs-before.json'));after=document(z.read(prefix+'inputs-after.json'))
        assert before==after==git_hashes(list(before)) and len(before)==695
        assert receipt['source_revision']==receipt['source_revision_after']==REV and receipt['source_tree_dirty'] is False
        assert not receipt['changed_inputs'] and not receipt['quarantined_prior_reports']
        assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(before)
        runtime=document(z.read(prefix+'runtime.json'))
        assert runtime['source_revision']==REV and runtime['source_tree_dirty'] is False
        assert receipt['runtime_receipt_sha256']==sha(z.read(prefix+'runtime.json'))
        module=next(x for x in receipt['modules'] if x['module']=='calf-ui')
        # The historical Native UI suite failed elsewhere. Preserve that overall
        # result; no marker/collection failure may be silently reclassified.
        assert not [e for e in receipt['errors'] if e.get('module')=='calf-ui' and
                    e['error']!='Failed, errored or unexpected skipped tests are not accepted by this verification gate']
        cases=[];reports=[];all_cases=[]
        for report in module['reports']:
            payload=z.read(report['path']);assert sha(payload)==report['sha256']
            parsed=lt.junit_cases(payload);all_cases.extend(parsed)
            assert all(report[k]==v for k,v in lt.case_counts(parsed).items())
            scoped=[c for c in parsed if c['classname'].split('.')[-1]=='TimePickerStateContractTest']
            if scoped:
                cases.extend(scoped);reports.append(report)
        order=lambda c:(c['classname'],c['name'])
        assert sorted(all_cases,key=order)==sorted(module['testcases'],key=order)
        normalized={re.sub(r'\[[^\]]+\]$','',c['name']) for c in cases}
        assert normalized==expected and len(cases)==len(normalized)==3 and len(reports)==1
        assert all(c['status']=='passed' for c in cases)
        collector=subprocess.check_output(['git','show',REV+':scripts/ci/library_tests.py'],cwd=ROOT).decode()
        assert 'if marker_counts[task] != 1:' in collector
        scopes.append({
            'run_id':run,'artifact_id':art,'slot':slot,'url':rv['html_url'],
            'source_revision':REV,'overall_run_conclusion':rv['conclusion'],
            'whole_suite_passed':receipt['passed'],'actual_command':receipt['command'],
            'actual_command_execution':receipt['execution'],'runtime':runtime,
            'artifact_path':raw.relative_to(ROOT).as_posix(),'artifact_sha256':sha(raw),
            'Git_bound_inputs':len(before),'before_after_inputs_identical_to_Git':True,
            'owning_scope_testcases':cases,'owning_scope_counts':lt.case_counts(cases),'owning_scope_reports':reports,
            'legacy_successful_marker_counters_not_archived':True,
            'Git_bound_collector_enforces_one_fresh_task_marker':True,
            'whole_module_collection_errors_preserved': [e for e in receipt['errors'] if e.get('module')=='calf-ui'],
        })

slots=[s['slot'] for s in scopes]
review={
    'schema_version':1,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
    'kind':'Lead original UI-009 source/compatibility/Git/ZIP/raw-XML acceptance review',
    'id':'UI-009','issue_number':123,'issue_url':issue['html_url'],
    'original_required_tests':finding['required_tests'],'original_dependencies':finding['dependencies'],
    'original_upstream_refs':finding['upstream_refs'],
    'previous_status':ledger['status'],'previous_remaining_preserved_verbatim':ledger['remaining'],
    'compatibility':ledger['compatibility'],'issue_body_sha256_before':sha(issue['body'].encode()),
    'issue_title_sha256_before':sha(issue['title'].encode()),'issue_labels_before':[x['name'] for x in issue['labels']],
    'requirements_review':[
        {'requirement':finding['required_tests'][0],'status':'passed-scoped-runtime',
         'methods':[{'class':'TimePickerStateContractTest','method':n,'passed_on_slots':slots}
                    for n in ['rejectsInvalidHoursAndMinutes','acceptsBoundaryValues']]},
        {'requirement':finding['required_tests'][1],'status':'passed-scoped-runtime',
         'methods':[{'class':'TimePickerStateContractTest','method':'saverRoundTripAndCorruptedInputValidation','passed_on_slots':slots}]},
    ],
    'source_revision_at_review':lt.git_revision(ROOT),'dirty_worktree':True,
    'immutable_runtime_revision':REV,'owning_current_input_hashes_identical_to_runtime':current,
    'owning_input_count':len(paths),'owning_inputs_held_during_review':all(sha(ROOT/n)==h for n,h in current.items()),
    'reviewed_immutable_runtime_scopes':scopes,'scoped_runtime_executions':12,'unique_source_methods':3,
    'acceptance':'Accepted for the original constructor/Saver finding only after pushed evidence/current preflight and exact GitHub closure readback. Both actuals execute; unrelated native-view/menu/state-owner/presentation findings stay open.',
    'review_script_sha256':sha(Path(__file__)),'junit_parser_sha256':sha(ROOT/'scripts/ci/library_tests.py'),
    'new_runtime_executions_by_this_review':0,'issues_closed_by_this_review':0,'release_readiness_certified':False,
    'limits':[
        'Historical overall Apple suite failed in other UI/native scenarios; individually passed state-constructor/Saver XML is accepted without relabeling the whole suite.',
        'Material JVM/Android-host and iOS actual state-model runtime tests. No device time-picker rendering, timezone/locale/hour-cycle preference, physical accessibility or state-owner replacement certification.',
        'Minute -1/0/59/60 and hour -1/0/23/24 construction plus valid SavedState roundtrip and rejected out-of-range saved minute. Not arbitrary serialized-input schema fuzzing.',
        'Existing constructor names/descriptors/Saver shape retained; newly rejected invalid minute is the deliberate correctness change. Complete Kotlin/Java/KLIB/Swift ABI and packaged consumer/minimum-platform/security/legal/release gates stay independent.',
        'The source-held new navigation test/profile and pending UIKit8ab82 application run are separate; neither is presented as execution of these historical state-model tests.',
    ],
}
assert review['owning_inputs_held_during_review']
with (OUT/'lead-timepicker-state-acceptance.json').open('x') as f:
    json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'id':'UI-009','accepted_requirements':len(review['requirements_review']),
                  'owning_unchanged_files':len(paths),'scoped_executions':12,'unique_source_methods':3,
                  'new_runtime_executions':0,'issues_closed':0},indent=2))
