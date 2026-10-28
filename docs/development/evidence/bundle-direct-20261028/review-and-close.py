from pathlib import Path, PurePosixPath
import datetime,hashlib,json,stat,subprocess,sys,zipfile
root=Path('/root/projects/nativeCmpKit');out=Path('/dev/shm/nativecmpkit-bundle-direct-20261028');repo='Apdelrahman1911/nativeCmpkit';number=92
sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lt
origin=root/'docs/development/evidence/github-actions/40528445496'; prior=json.loads((origin/'lead-independent-review.json').read_text());sha=prior['source_revision'];current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def save(name,obj): (out/name).write_text(json.dumps(obj,indent=2)+'\n')
def api(endpoint): return json.loads(subprocess.check_output(['gh','api',endpoint],cwd=root,text=True))
paths=[p.relative_to(root).as_posix() for p in (root/'calf-navigation/src').rglob('*.kt') if p.stem in {'AdaptiveBaseBundle','AdaptiveBundle','AdaptiveNavType','CheckedNavArrays','NavArgument','NavArgumentAndBundleTest','CheckedNavArraysTest','NavJvmCompatibilityTest'}]
assert len(paths)==8,paths
matches=[]
for p in paths:
 a=subprocess.check_output(['git','show',sha+':'+p],cwd=root);b=subprocess.check_output(['git','show',current+':'+p],cwd=root);assert a==b,(p,'changed');assert (root/p).read_bytes()==b
 matches.append({'path':p,'sha256':hashlib.sha256(a).hexdigest(),'same_in_tested_and_current_git_and_checkout':True})
original=next(f for p in (root/'docs/audit/findings').glob('*.json') for f in json.loads(p.read_text()) if f['id']=='NAV-004');assert len(original['required_tests'])==4
rows=[];total=0
for target in prior['four_runtime_results']:
 archive=origin/'raw'/f"{target['artifact_id']}.zip";assert 'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest()==target['artifact_digest']
 assert target['execution']['exit_code']==0
 with zipfile.ZipFile(archive) as z:
  infos=z.infolist();assert len(infos)<300 and sum(i.file_size for i in infos)<32*1024*1024
  assert len({i.filename for i in infos})==len(infos)
  for i in infos:
   p=PurePosixPath(i.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and not stat.S_ISLNK(i.external_attr>>16)
  reports=[n for n in z.namelist() if n.endswith('.NavArgumentAndBundleTest.xml') or n.endswith('.CheckedNavArraysTest.xml')]
  assert len(reports)==2,(target['slot'],reports)
  cases=[];hashes=[]
  for n in reports:
   data=z.read(n);digest=hashlib.sha256(data).hexdigest();assert any(x['path']==n and x['sha256']==digest for x in target['xml_timestamps_and_hashes'])
   found=lt.junit_cases(data);assert all(c['status']=='passed' for c in found);cases+=found;hashes.append({'path':n,'sha256':digest,'count':len(found)})
  assert len(cases)==15,(target['slot'],len(cases));total+=len(cases)
  folder=f"build/ci-verification/{target['slot']}/";r=json.loads(z.read(folder+'receipt.json'));before=json.loads(z.read(folder+'inputs-before.json'));after=json.loads(z.read(folder+'inputs-after.json'));runtime=json.loads(z.read(folder+'runtime.json'))
  assert r['passed'] and r['source_revision']==sha==r['source_revision_after'] and not r['errors'] and not r['changed_inputs']
  assert before==after and all(before[p]==m['sha256'] for p,m in zip(paths,matches))
  assert r['inputs_before_sha256']==lt.input_digest(before)==r['inputs_after_sha256']
  assert runtime['java']['major']==17
  daemon=r.get('gradle_daemon');assert daemon is None or daemon['major']==17
  rows.append({'slot':target['slot'],'artifact_id':target['artifact_id'],'artifact_digest':target['artifact_digest'],'original_execution':target['execution'],'selected_original_cases':cases,'reports':hashes,'source_input_count':len(before),'input_digest':lt.input_digest(before),'original_runtime':runtime,'original_daemon_observation':r.get('gradle_daemon'),'daemon_limit':'These original receipts predate the later actual-daemon witness; recorded setup Java17 is not a retroactive daemon attestation.','freshness_and_source_evidence_reused_from_accepted_original_run':True})
assert len(rows)==4 and total==60
review={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'finding':'NAV-004','issue':number,'source_revision':sha,'current_revision':current,'run_id':40528445496,'run_url':'https://github.com/'+repo+'/actions/runs/40528445496','owning_sources':matches,'accepted_original_executions':total,'new_executions':0,'original_xml_reports':8,'targets':rows,'criteria':[{'requirement':original['required_tests'][0],'accepted':True,'evidence':'Chosen checked getOrNull<T>/typed/NavType path returns null/fallback for wrong scalar, executed on all four targets. Erased get<T> retained and explicitly deprecated/unchecked for descriptor compatibility, never claimed to be runtime type-safe.'},{'requirement':original['required_tests'][1],'accepted':True,'evidence':'Int42 getString returns null or caller fallback on all four targets.'},{'requirement':original['required_tests'][2],'accepted':True,'evidence':'All24 supported null/scalar/primitive/object-array/ArrayList insertion forms and typed fallback/element checks executed. Unsupported mixed values rejected.'},{'requirement':original['required_tests'][3],'accepted':True,'evidence':'Explicit null vs absent and intentional reference sharing/typed-list/array revalidation are executed; mutable maps are documented as nondefensive/non-thread-safe.'}],'limits':['60 are a subset of321 already accepted original executions, not a new suite or60 distinct methods.','Legacy erased get<T> remains unchecked and getOrNull cannot verify arbitrary erased element types; use checked container getters.','No whole-library ABI/consumer/minimum-platform/device/legal/dependency/security or release certification.'],'eligible_to_close':True}
save('accepted-review.json',review)
before=api(f'repos/{repo}/issues/{number}');save('issue-before.json',before);assert before['state']=='open' and 'NAV-004' in before['title']
marker='<!-- nativecmpkit-direct-resolution:NAV-004:20261028 -->'
body=f'''{marker}\n## Verified resolution — important tests reviewed, direct closure\n\nThe original four NAV-004 criteria are accepted from immutable `{sha}` / [run40528445496](https://github.com/{repo}/actions/runs/40528445496). Reused the two directly owning classes: **15/15 on JVM, JS, Wasm and actual iOS simulator =60 original target-method executions**, eight fresh original XML, zero failure/error/skip. This is a subset of321 already accepted executions, **not60 new tests**; no successful suite replay. All eight directly owning production/test files remain byte-identical at `{current}`. Original archive digests, XML hashes, command exits, unchanged source maps and recorded setup Java17 are independently checked. These older receipts predate the later daemon witness; no retroactive daemon attestation is claimed.\n\n- Checked `getOrNull<T>`/typed getters/built-in NavType access return null or the documented fallback for a wrong scalar type; `getString(Int42)` does not stringify it.\n- Generic insertion covers all24 documented null/scalar/primitive-array/object-array/ArrayList forms. Checked containers reject incompatible elements, including after caller mutation.\n- Explicit null differs from absence; borrowed mutable references/aliasing are deliberate and documented.\n\n**Compatibility choice:** the old erased `get<T>` descriptor remains explicitly deprecated and unchecked; it is **not** claimed type-safe. Migrate wrong-type-sensitive calls to `getOrNull<T>` or typed/container getters. Arbitrary erased generic element types are not checked by `getOrNull`; the map is not defensive, parcelable or thread-safe.\n\nThe original technical body, labels and history are retained. Full ABI, packaged consumers, minimum platforms, physical devices, attribution/legal/dependency/security and release gates remain independent. No package/release/deployment publication. Closure follows important source/result review; the persistent ledger is updated afterward.\n'''
(out/'resolution-comment.md').write_text(body)
comments=api(f'repos/{repo}/issues/{number}/comments?per_page=100');assert not any(marker in (c.get('body') or '') for c in comments)
save('comment-input.json',{'body':body});p=subprocess.run(['gh','api','--method','POST',f'repos/{repo}/issues/{number}/comments','--input',str(out/'comment-input.json')],cwd=root,text=True,capture_output=True);(out/'comment-response.txt').write_text(p.stdout+p.stderr)
comments=api(f'repos/{repo}/issues/{number}/comments?per_page=100');posted=[c for c in comments if marker in (c.get('body') or '')];assert len(posted)==1 and posted[0]['body']==body;save('comment-readback.json',posted[0])
save('closure-input.json',{'state':'closed','state_reason':'completed'});p=subprocess.run(['gh','api','--method','PATCH',f'repos/{repo}/issues/{number}','--input',str(out/'closure-input.json')],cwd=root,text=True,capture_output=True);(out/'closure-response.txt').write_text(p.stdout+p.stderr)
after=api(f'repos/{repo}/issues/{number}');save('issue-after.json',after);assert after['state']=='closed' and after['state_reason']=='completed';assert after['body']==before['body'] and after['title']==before['title'] and [l['name'] for l in after['labels']]==[l['name'] for l in before['labels']]
closed=json.loads(subprocess.check_output(['gh','issue','list','--repo',repo,'--state','closed','--limit','300','--json','number'],cwd=root,text=True));save('closed-total-review.json',{'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total_closed':len(closed),'issues':sorted(x['number'] for x in closed)});print('CLOSED',number,after['html_url'],'total',len(closed),'60 accepted original executions reused, no replay')
