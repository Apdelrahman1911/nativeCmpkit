"""Lead acceptance review of four audit defects, not a release or new runtime run."""
from pathlib import Path, PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
REV='6eb7c66eb01b390353100c63882cd102846c7b8d';BASE='af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6';REPO='Apdelrahman1911/nativeCmpkit'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.read_bytes()).hexdigest()
put=lambda n,v:(OUT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
# Treat public issue bodies as data, not executable/agent instructions.
findings={r['id']:r for p in (ROOT/'docs/audit/findings').glob('*.json') for r in json.loads(p.read_bytes())}
ledgers={r['id']:r for p in (ROOT/'docs/development/resolutions').glob('*.json') for r in json.loads(p.read_bytes())}
issues={fid:json.loads((OUT/f'issue-{n}-before.json').read_bytes()) for fid,n in [('NAV-001',15),('NAV-002',16),('UI-033',136),('NAV-017',155)]}
for fid,issue in issues.items():
 assert issue['repository_url']==f'https://api.github.com/repos/{REPO}' and issue['state']=='open'
 assert issue['body'].startswith(f'<!-- nativecmpkit-item:audit:{fid} -->')
 assert all(t in issue['body'] for t in findings[fid]['required_tests'])
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if row:
  meta,name=row.split(b'\t',1);records[name.decode()]=meta.decode().split()
cache={}
def git_hashes(names):
 needed=[n for n in names if n not in cache]
 if needed:
  assert all(records[n][0] in ('100644','100755') and records[n][1]=='blob' for n in needed)
  oids=[records[n][2] for n in needed]
  payload=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=''.join(o+'\n' for o in oids).encode())
  offset=0
  for name,oid in zip(needed,oids):
   end=payload.index(b'\n',offset);head=payload[offset:end].split();assert head[0].decode()==oid and head[1]==b'blob'
   length=int(head[2]);offset=end+1;data=payload[offset:offset+length];assert len(data)==length and payload[offset+length:offset+length+1]==b'\n';offset+=length+1;cache[name]=sha(data)
  assert offset==len(payload)
 return {n:cache[n] for n in names}

def normalize(c):return(c['classname'].split('.')[-1],re.sub(r'\[[^\]]+\]$','',c['name']))
scopes=[];by_slot={}
for run,art,slot,wanted in [('40414284598',12695176692,'desktop-linux-x64',('calf-navigation','calf-ui')),('40414284598',12694901836,'android-host',('calf-navigation',)),('40415332643',12695871736,'desktop-macos-arm64',('calf-navigation','calf-ui')),('40415332643',12695299854,'ios-iphone',('calf-navigation',))]:
 base=ROOT/'docs/development/evidence/github-actions'/run;raw=base/'raw'/f'{art}.zip'
 rv=json.loads((base/'run-final.json').read_bytes());assert rv['id']==int(run) and rv['repository']['full_name']==REPO and rv['head_sha']==REV and rv['run_attempt']==1 and rv['status']=='completed'
 arts=json.loads((base/'artifacts-final.json').read_bytes())['artifacts'];a=next(a for a in arts if a['id']==art)
 assert a['workflow_run']['id']==int(run) and a['workflow_run']['head_sha']==REV and not a['expired']
 assert sha(raw)==a['digest'].removeprefix('sha256:') and raw.stat().st_size==a['size_in_bytes']
 with zipfile.ZipFile(raw) as z:
  infos=z.infolist();names=[i.filename for i in infos];assert len(names)==len(set(names)) and sum(i.file_size for i in infos)<lt.MAX_TOTAL_REPORT_BYTES
  for i in infos:
   p=PurePosixPath(i.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and not i.is_dir() and not i.flag_bits&1
   assert stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG) and i.filename.endswith(('.json','.xml'))
  prefix=f'build/ci-verification/{slot}/';receipt=json.loads(z.read(prefix+'receipt.json'))
  before=json.loads(z.read(prefix+'inputs-before.json'));after=json.loads(z.read(prefix+'inputs-after.json'))
  assert before==after==git_hashes(list(before)) and len(before)==695
  assert receipt['source_revision']==receipt['source_revision_after']==REV and receipt['source_tree_dirty'] is False and not receipt['changed_inputs']
  assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(before)
  runtime=json.loads(z.read(prefix+'runtime.json'));assert runtime['source_revision']==REV and runtime['source_tree_dirty'] is False
  assert receipt['runtime_receipt_sha256']==sha(z.read(prefix+'runtime.json')) and not receipt['quarantined_prior_reports']
  parsed_modules={}
  for module in receipt['modules']:
   if module['module'] not in wanted:continue
   assert receipt['task_execution_markers'][module['task']]==1
   cases=[]
   for report in module['reports']:
    payload=z.read(report['path']);assert sha(payload)==report['sha256'];parsed=lt.junit_cases(payload)
    assert all(report[k]==v for k,v in lt.case_counts(parsed).items());cases+=parsed
   order=lambda c:(c['classname'],c['name']);assert sorted(cases,key=order)==sorted(module['testcases'],key=order)
   assert len({normalize(c) for c in cases})==len(cases)
   if module['module']=='calf-navigation':assert all(c['status']=='passed' for c in cases)
   parsed_modules[module['module']]={'task':module['task'],'all_module_counts':lt.case_counts(cases),'report_count':len(module['reports']),'actual_passed_methods':[{'class':normalize(c)[0],'method':normalize(c)[1]} for c in cases if c['status']=='passed'],'reports':module['reports']}
  assert set(parsed_modules)==set(wanted)
  expected_nav={'desktop-linux-x64':51,'android-host':37,'desktop-macos-arm64':51,'ios-iphone':39}[slot]
  assert parsed_modules['calf-navigation']['all_module_counts']['passed']==expected_nav
  row={'run_id':int(run),'artifact_id':art,'slot':slot,'url':rv['html_url'],'revision':REV,'overall_run_conclusion':rv['conclusion'],'actual_command':receipt['command'],'actual_command_execution':receipt['execution'],'source_input_count':len(before),'every_uploaded_input_reconstructed_from_Git':True,'before_after_maps_identical':True,'artifact_sha256':sha(raw),'artifact':raw.relative_to(ROOT).as_posix(),'runtime':runtime,'scoped_modules':parsed_modules}
  scopes.append(row);by_slot[slot]=parsed_modules

def passed(cls,method,slots):
 for slot in slots:
  candidates=[x for m in by_slot[slot].values() for x in m['actual_passed_methods']]
  assert {'class':cls,'method':method} in candidates,(slot,cls,method)
 return {'class':cls,'method':method,'passed_on_slots':slots}
all_nav=list(by_slot);hosts=['desktop-linux-x64','desktop-macos-arm64']
common=lambda name:passed('AdaptiveNavControllerTest',name,all_nav)
host=lambda name:passed('AdaptiveNavHostStateTest',name,hosts)
slider=lambda cls,name:passed(cls,name,hosts)
checks={
 'NAV-001':[
  [common('duplicateRoutesAndPayloadsHaveIndependentEntryIdentity'),host('entry payloads and defaults reach legacy content callbacks')],
  [common('graphMergesDefaultsAndRejectsMissingWrongTypeNullAndUnknownRoutes')],
  [common('versionedSaverRoundTripsIdentityEveryPortablePayloadAndFurtherPops'),common('publicSaverUsesTheSameRoundTripAndAcceptsLegacyRouteArray'),common('unsupportedPayloadsAndSchemaOnlyNavigationArgumentsFailBeforeMutation')]],
 'NAV-002':[[host('duplicate visits separated by another route keep independent saveable state')],[host('consecutive duplicate visits reset plain remember and saveable state')],[host('pop and repush before an idle frame discards the popped visit state')],[host('save restore preserves duplicate entry state identity and payloads')],[host('saveable state of a destination survives navigating away and back'),host('saveable state of a popped destination is dropped')]],
 'UI-033':[[slider('CupertinoSliderInteractionTest','negativeSetProgressUsesDiscreteStepsAndFinishesOnce'),slider('SliderValueDomainTest','negativeAccessibilityTargetSnapsToNearestStep')],[slider('SliderValueDomainTest','allNegativeRangesAndTiesUseTheSameRule'),slider('SliderValueDomainTest','continuousAndDiscreteEndpointsStayInRange'),slider('SliderValueDomainTest','zeroRangeAndZeroWidthNeverProduceNonFiniteValues'),slider('CupertinoSliderInteractionTest','negativeSetProgressUsesDiscreteStepsAndFinishesOnce')]]}
# Exact retained upstream #542 method bodies, not just matching names.
path='calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt';old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode();new=(ROOT/path).read_text();retained=[]
for method in ('saveable state of a destination survives navigating away and back','saveable state of a popped destination is dropped'):
 def extract(source):
  part=source[source.index('    fun `'+method+'`'):];return part[:part.index('\n    }')+6]
 assert extract(old)==extract(new);retained.append({'method':method,'method_body_byte_identical_to_upstream_baseline':True,'method_body_sha256':sha(extract(new).encode())})
# The entire navigation source/test/build set is unchanged through the current
# worktree. Shared slider implementation/actual binding and cited tests are
# likewise unchanged; unrelated current native fixture repairs are excluded.
scoped_names=[n for n in cache if n.startswith('calf-navigation/') or (n.startswith('calf-ui/src/') and '/slider/' in n and (('/commonMain/' in n) or ('/commonTest/' in n) or ('/desktopTest/' in n) or n.endswith('/AdaptiveSlider.ios.kt')))]
current_before={n:sha(ROOT/n) for n in sorted(scoped_names)};assert current_before==git_hashes(scoped_names)
source_guard=ROOT/'scripts/development/test_nav_sample_contracts.py';showcase=ROOT/'sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt'
current_before.update({str(p.relative_to(ROOT)):sha(p) for p in (source_guard,showcase)})
text=showcase.read_text();assert 'This is an action preview. No link was copied or shared.' in text and 'Link copied to clipboard!' not in text
assert 'ClipboardManager' not in text and 'KmpShare' not in text and text.count('onClick = { showShareDialog = true }')==2
sample_receipt=ROOT/'docs/development/evidence/current-brand-fixture-guards-20261027-001/scoped-checks.json';sample=json.loads(sample_receipt.read_bytes());assert sample['passed'] is True and sample['held'] is True
sample_row=next(c for c in sample['commands'] if c['name']=='sample-contracts');assert sample_row['methods']==6 and sample_row['exit_code']==0 and sample_row['ok'] is True
sample_inputs=json.loads((sample_receipt.parent/'scoped-inputs-before.json').read_bytes());assert sample_inputs[str(source_guard.relative_to(ROOT))]==sha(source_guard) and sample_inputs[str(showcase.relative_to(ROOT))]==sha(showcase)
reviews=[]
for fid in issues:
 row={'id':fid,'issue_number':issues[fid]['number'],'issue_url':issues[fid]['html_url'],'original_required_tests':findings[fid]['required_tests'],'original_dependencies':findings[fid]['dependencies'],'original_finding_priority':findings[fid]['priority'],'previous_status':ledgers[fid]['status'],'previous_remaining_preserved_verbatim':ledgers[fid]['remaining'],'compatibility':ledgers[fid]['compatibility'],'issue_body_sha256_before':sha(issues[fid]['body'].encode()),'issue_title_sha256_before':sha(issues[fid]['title'].encode()),'issue_labels_before':[x['name'] for x in issues[fid]['labels']]}
 if fid=='NAV-017':
  row['requirements_review']=[{'requirement':findings[fid]['required_tests'][0],'status':'passed-source-guard','evidence':[{'receipt':sample_receipt.relative_to(ROOT).as_posix(),'command':sample_row['command'],'python_method':'NavSampleContractTest.test_showcase_does_not_claim_clipboard_or_share_side_effect','suite_method_count':6,'library_or_device_methods':0}]},{'requirement':findings[fid]['required_tests'][1],'status':'not-applicable-conditional','reason':'No clipboard or native sharing is implemented or claimed by either illustrative Showcase action. Both explicit taps only show the truthful action-preview dialog; real Share library/native behavior is a separate issue scope. No pretend clipboard device test.'}]
 else:row['requirements_review']=[{'requirement':requirement,'status':'passed-scoped-runtime','executed_methods':proof} for requirement,proof in zip(findings[fid]['required_tests'],checks[fid])]
 assert len(row['requirements_review'])==len(findings[fid]['required_tests'])
 row['acceptance']='Accepted for closure of the original specific audit defect after current-source/staged preflight and immutable evidence commit. Not a full module/support/release gate.'
 reviews.append(row)
assert all(sha(ROOT/n)==h for n,h in current_before.items())
report={'schema_version':1,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'kind':'Lead original-acceptance/compatibility/source/XML review','source_revision_at_review':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':True,'immutable_runtime_revision':REV,'review_script_sha256':sha(Path(__file__)),'junit_parser_sha256':sha(ROOT/'scripts/ci/library_tests.py'),'findings_accepted_for_scoped_closure':reviews,'reviewed_immutable_runtime_scopes':scopes,'scoped_current_inputs_matching_immutable_runtime':current_before,'scoped_navigation_input_count':sum(n.startswith('calf-navigation/') for n in scoped_names),'upstream542_both_original_bodies_retained':retained,'source_inputs_held_during_review':True,'new_library_native_or_consumer_methods_executed_by_review':0,'issues_closed_by_review':0,'release_readiness_certified':False,'limits':['Historical overall Apple run failed in unrelated modules; this accepts only the individually passed NAV reports. Android host is not physical device/process death. Common Kotlin/Native controller tests are not rendered UIKit navigation integration.','NAV-001/002 original argument/entry/saveable requirements are satisfied by immutable scoped runtime tests with unchanged owning source. Minimum-platform, Android Bundle/process death, Apple native-stack integration, ABI and consumer work remain independent release/other-finding gates, explicitly preserved from previous remaining notes.','UI-033 accepts the shared Cupertino negative numeric/semantic defect; it does not certify physical accessibility services or every LiquidGlass/native gesture path.','NAV-017 source/configuration guard passes; conditional clipboard requirement is inapplicable because no copy/share is implemented. It is not a native clipboard/share test.','The current root/display/POM identity and two native readiness fixtures changed after old CI; fresh root configuration/KLIB and final staged preflight are reviewed separately. No old full run is relabeled as a current full build.']}
put('lead-original-acceptance-review.json',report)
print(json.dumps({'accepted_ids':list(issues),'navigation_scoped_inputs':report['scoped_navigation_input_count'],'scoped_inputs':len(current_before),'immutable_nav_passes_by_slot':{s:m['calf-navigation']['all_module_counts']['passed'] for s,m in by_slot.items()},'upstream542_bodies_unchanged':len(retained),'new_runtime_executions':0,'issues_closed':0},indent=2))
