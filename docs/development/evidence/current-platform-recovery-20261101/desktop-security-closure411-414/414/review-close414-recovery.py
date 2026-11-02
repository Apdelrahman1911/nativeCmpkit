"""Literal BUILD-002 review and one-shot closure; never replays native tests."""
import datetime, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET, zipfile
from pathlib import Path
ROOT=Path('/root/projects/nativeCmpKit'); BASE=Path('/root/nativecmpkit-native-reviews-20261101'); OUT=Path(__file__).parent
REV='ae7893816f147ed7b54db0676c77e500a3346056'; REPO='Apdelrahman1911/nativeCmpkit'
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as library
from desktop_policy_creation_source_projection import source_before_policy_creation
from desktop_windows_tls_source_projection import source_before_windows_tls
sys.path.insert(0,str(ROOT/'scripts/migration')); from github_json import json_pages
checks=[]
def check(name,value):
 if not value: raise AssertionError(name)
 checks.append(name)
def read(p): return json.loads(Path(p).read_bytes())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name,value):
 with (OUT/name).open('x') as f: json.dump(value,f,indent=2,sort_keys=True); f.write('\n')
def pointer(n): return Path((BASE/n).read_text().strip())
def api(name, endpoint, method='GET', fields=None, paginate=False):
 argv=['gh','api','--method',method,endpoint]
 if paginate: argv+=['--paginate']
 if fields:
  p=OUT/(name+'.request.json');save(p.name,fields);argv+=['--input',str(p)]
 save(name+'.attempt.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':method,'endpoint':endpoint,'paginate':paginate,'automatic_retries':0})
 p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=90)
 for suffix,value in [('response.json',p.stdout),('stderr',p.stderr),('exit-code',(str(p.returncode)+'\n').encode())]:
  with (OUT/(name+'.'+suffix)).open('xb') as f:f.write(value)
 if p.returncode: raise RuntimeError(name+' refused; reconcile preserved response before retry')
 return json_pages(p.stdout.decode()) if paginate else json.loads(p.stdout)
check('prior414 refusal stopped before comment/closure mutations',not any(p.name.startswith(('comment144','close144','issue144-after','ACCEPTANCE414','CLOSURE414')) for p in OUT.iterdir()))
save('FIRST414-refusal.json',{'original_session':76975,'exit_code':1,'error':'Original BUILD-001 dependency already verified/closed; no duplicate closure','cause':'Mistaken dependency issue143 is UI-045. Original issue-map maps BUILD-001 to issue1. No mutations were attempted.','original_refused_response_sha256':sha((OUT/'dependency143-before.response.json').read_bytes()),'native_or_library_failure':False})
check('exact clean current HEAD',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==REV and not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT))
frozen=read(pointer('SECURITY411-CURRENT-DISPATCH')/'library-inputs.json')
check('all1223 original current inputs still held',library.snapshot_inputs(ROOT)==frozen and len(frozen)==1223)
issue_map=read(ROOT/'docs/migration/issue-map.json');rows=issue_map['items']; entry=next(x for x in rows if x['key']=='audit:BUILD-002');dep=next(x for x in rows if x['key']=='audit:BUILD-001')
check('original identifiers map BUILD002 to144 and BUILD001 to1',entry['number']==144 and dep['number']==1)
before=api('issue144-reconciled-before',f'repos/{REPO}/issues/144');dep_before=api('dependency1-reconciled-before',f'repos/{REPO}/issues/1')
check('original BUILD001 dependency already completed with correct identity',dep_before['state']=='closed' and dep_before['state_reason']=='completed' and '<!-- nativecmpkit-item:audit:BUILD-001 -->' in dep_before['body'])
check('144 original open body/title/authorship/timestamps retained',before['state']=='open' and sha(before['body'].encode())==entry['body_sha256']=='bf793c9eecadce9c25bf2e814427bab72cd63807460ca896bf44ab615f508b18' and before['title']==entry['title'] and before['user']['login']==entry['github_author'] and before['created_at']==entry['github_created_at'])
refs={}
def authority(name,p):
 x=read(p);refs[name]={'path':str(p),'sha256':sha(Path(p).read_bytes())};return x
r388=authority('macOS_originals388',pointer('SECURITY388-CURRENT-REVIEW')/'REVIEW388.json')
r404=authority('macOS_policy404',pointer('SECURITY404-CURRENT-REVIEW')/'REVIEW404.json')
r407=authority('Windows_LinuxARM64_originals407',pointer('SECURITY407-CURRENT-REVIEW')/'REVIEW407.json')
r413=authority('Windows_TLS_original413',pointer('SECURITY413-CURRENT-REVIEW')/'REVIEW413.json')
a389=authority('macOS_advisory389',pointer('SECURITY389-CURRENT-ADVISORY')/'ADVISORY389.json')
a408=authority('Windows_LinuxARM64_advisory408',pointer('SECURITY408-CURRENT-ADVISORY')/'ADVISORY408.json')
legacy=authority('old_native_applicability',ROOT/'docs/development/evidence/javafx21-current-security-20261101/review002/runtime-evidence-applicability.json')
oldmatrix=authority('old_literal_matrix',ROOT/'docs/development/evidence/javafx21-current-security-20261101/review002/requirement-matrix.json')
oldfacts=authority('old_Linux_graph_advisories',ROOT/'docs/development/evidence/javafx21-current-security-20261101/review001/review-facts.json')
tls034=authority('accepted_Linux_TLS034',ROOT/'docs/development/evidence/current-platform-recovery-20261101/tls-actual034/independent-review.json')
check('C1 prior Linux24/72 graph142 advisory observations qualify unchanged dependency selection',oldfacts['reused_graph']['all_original_archive_hashes_match'] and oldfacts['reused_graph']['all_six_modules_aligned_at_current_pin'] and oldfacts['reused_graph']['configurations']==72 and oldfacts['reused_graph']['unique_Maven_coordinates']==142 and oldfacts['reused_graph']['coordinate_matches']==0)
for host in r388['slots']+r407['hosts']:
 check('C1 actual full runtime24 compile-test48 graph '+host['slot'],len(host['graphs'])==2 and {(g['phase'],g['configurations']) for g in host['graphs']}=={('runtime',24),('compile-test',48)} and all(g['execution']['exit_code']==0 for g in host['graphs']))
check('C1 other four supported hosts actual graphs complete',len({h['slot'] for h in r388['slots']+r407['hosts']})==4 and r388['passed_source_results_review'] and r407['passive_check_count']==66)
for rel in ['gradle/libs.versions.toml','convention-plugins/src/main/kotlin/DesktopJavaFx.kt','convention-plugins/src/main/kotlin/desktop.javafx.gradle.kts']:
 check('C1 current dependency declaration unchanged '+rel,subprocess.check_output(['git','show','3a3a93bd:'+rel],cwd=ROOT)==(ROOT/rel).read_bytes())
check('C1 exact four plus four new advisories HTTP200 no matches',a389['HTTP_status']==a408['http_status']==200 and a389['new_exact_coordinates_queried']==a408['queries']==4 and a389['matched_coordinates']==a408['coordinate_matches']==0 and a408['prior_accepted_queries_replayed']==0)
check('C1 union150 exact coordinates accepted without replay',len({(r['name'],r['version']) for r in a389['results']+a408['results']})==8 and 142+8==150)
for r in legacy['existing_independent_review_references']:
 check('C2 prior acceptance authority hash '+r['path'],sha((ROOT/r['path']).read_bytes())==r['sha256'])
for r in legacy['original_XML_readbacks']:
 if 'archive' in r:
  ar=ROOT/r['archive']['path'];check('C2 cached original archive hash '+ar.name,sha(ar.read_bytes())==r['archive']['sha256'])
  with zipfile.ZipFile(ar) as z:raw=z.read(r['path'])
 else:raw=(ROOT/r['path']).read_bytes()
 check('C2 cached original XML hash '+r['path'],sha(raw)==r['sha256'] and b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw)
 tree=ET.fromstring(raw);cases=tree.findall('testcase')
 check('C2 retained original case sets '+r['path'],[(c.attrib['classname'],c.attrib['name']) for c in cases]==[(c['classname'],c['name']) for c in r['cases']])
check('C2 legacy bounded media/navigation4 and Linux cookie/policy qualify',all(len(next(a for a in oldmatrix['C2']['areas'] if a['area']==area)['accepted_hosts'])==4 for area in ['media','navigation']) and all(next(a for a in oldmatrix['C2']['areas'] if a['area']==area)['accepted_hosts']==['desktop-linux-x64'] for area in ['cookies','JavaScript policy']))
check('C2 original Linux TLS/rendering1 passed',tls034['actual_result']['passed_methods']==1 and tls034['actual_result']['gradle_exit_code']==0 and tls034['actual_result']['failed_methods']==tls034['actual_result']['errors']==tls034['actual_result']['skips']==0)
check('C2 original TLS method remains exact across all hosts',sha((ROOT/'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt').read_bytes())=='00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c')
check('C2 macOS TLS/cookie4 accepted and policies2 recovered',r388['accepted_passes']==4 and all(o['passed'] for h in r388['slots'] for o in h['outcomes'] if o['key'] in ['tls-rendering','cookie']) and r404['native_passed']==2 and all(h['native_passed']==1 and h['execution']['exit_code']==0 for h in r404['hosts']))
check('C2 LinuxARM64 TLS rendering cookie policy media4 and Windows cookie policy2 accepted',r407['new_native_passed']==6 and all(o['status']=='passed' for h in r407['hosts'] for o in h['outcomes'] if h['slot']=='desktop-linux-arm64' or o['key']!='tls-rendering'))
check('C2 final Windows TLS original1 success actual input/XML native review',r413['all_native_accepted'] and r413['native_passed']==1 and r413['execution']['exit_code']==0 and r413['passive_check_count']==29 and r413['source_sha']==REV)
bindings=authority('C2_current_scope_binding',pointer('SECURITY409-CURRENT-PREPARATION')/'C2-prior25-current-binding-observation.json')
for r in bindings['rows']:
 raw=(ROOT/r['path']).read_bytes();check('C2 current scoped source held '+r['path'],sha(raw)==r['current_sha256'])
 if r['exact']:check('C2 unchanged legacy scoped source '+r['path'],sha(raw)==r['old_sha256'])
 elif r['exact_policy_and_windows_inverse_to_ff4f']:check('C2 exact inverse retains old criteria '+r['path'],sha(source_before_policy_creation(r['path'],raw))==r['old_sha256'])
 elif r['path'].endswith('OwnedDesktopTlsFixture.kt'):check('C2 owning TLS helper exact Windows inverse',sha(source_before_windows_tls(r['path'],raw))==r['old_sha256'])
 else:check('C2 current redirect source exact accepted ARM native348',raw==subprocess.check_output(['git','show','51a6d8cc93bd01d7118b2c524bdccea49276904e:'+r['path']],cwd=ROOT))
check('C2 explicit19of25 unchanged and six classified deltas not whole-map equivalence',bindings['count']==25 and bindings['exact']==19)
check('C3 unsupported sandboxed untrusted code boundary adopted','NativeCmpKit does not support sandboxed execution of untrusted desktop code.' in (ROOT/'docs/platforms/desktop.md').read_text())
check('current inputs still held before closure',library.snapshot_inputs(ROOT)==frozen)
save('ACCEPTANCE414.json',{'schema_version':1,'issue':144,'finding':'BUILD-002','source_sha':REV,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_original_criteria_accepted':True,'criteria':{'C1':'All five actual24+48 host graphs, six aligned JavaFX21.0.13 modules/classifiers;150-coordinate OSV union no matches. Only eight differing coordinates queried; accepted142 reused.','C2':'Bounded native media, TLS, cookies, navigation, disabled/enabled JavaScript policy, painted rendering on all five supported Desktop hosts; prior applicable passes reused, final failed-only Windows TLS1 now passes.','C3':'Documented unsupported sandboxed untrusted desktop-code execution.'},'authorities':refs,'checks':checks,'passive_check_count':len(checks),'native_tests_during_review':0,'original_redownloads':0,'prior414_refusal_preserved':True,'limits':['No engine-wide exploit, OS sandbox, all TLS protocols/codecs/physical GPU, independent artifact provenance, legal, package-consumer/API-ABI or release certification.','#64 remains open: private cancellation artifact not adopted by ordinary consumers.'],'release_allowed':False})
body='''Verified and completed **BUILD-002** against all three original acceptance criteria at `ae7893816f147ed7b54db0676c77e500a3346056`.

- **C1:** All five supported Desktop hosts have full resolved runtime/compile/test graphs (24 +48 configurations per host), six aligned JavaFX **21.0.13** modules/classifiers, and a **150-coordinate** exact OSV inventory with no matches. Accepted Linux142 queries were reused; only eight genuinely differing host coordinates were queried.
- **C2:** Native media/resource lifetime, trusted/untrusted TLS, cookies, navigation, JavaScript off/on policy and painted rendering now have bounded regressions on all five hosts. The last failed-only Windows TLS method passes **1/1**, original XML1, Gradle0/341.02s in [41545807583](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41545807583). Original trust/error/zero-HTTP/rendering/recovery/cleanup predicates are unchanged; 29 passive original-source/results checks and all1,223 frozen inputs qualify it. The focused classifier regressions also pass3/3. Prior accepted native methods/graphs were not replayed.
- **C3:** [Desktop trust boundary](https://github.com/Apdelrahman1911/nativeCmpkit/blob/development/preview-hardening/docs/platforms/desktop.md#untrusted-desktop-code-execution) explicitly does not support sandboxed execution of untrusted desktop code.

Evidence: [macOS original graphs/TLS/cookies](https://github.com/Apdelrahman1911/nativeCmpkit/tree/development/preview-hardening/docs/development/evidence/current-platform-recovery-20261101/desktop-security-originals385-395), [macOS policies](https://github.com/Apdelrahman1911/nativeCmpkit/tree/development/preview-hardening/docs/development/evidence/current-platform-recovery-20261101/desktop-policy-native402-404), [Windows/Linux ARM64 graphs, native subsets, advisory delta and focused recovery](https://github.com/Apdelrahman1911/nativeCmpkit/tree/development/preview-hardening/docs/development/evidence/current-platform-recovery-20261101/desktop-security-win-arm405-410). The final original/criterion/readback archive will be added alongside them as `desktop-security-closure411-414`.

Earlier failed runs remain failed. Zero advisory matches and bounded regressions are not engine-wide security, licensing, package-consumer/API–ABI or release certification. **#64 remains open** because its private cancellation candidate is not activated by ordinary consumer dependencies. No release, package or deployment is published by this closure. Original issue description, attribution and labels are preserved.'''
comment=api('comment144-resolution',f'repos/{REPO}/issues/144/comments','POST',{'body':body})
check('resolution comment exact server readback',comment['body']==body and comment['user']['login']==before['user']['login'])
closed=api('close144-completed',f'repos/{REPO}/issues/144','PATCH',{'state':'closed','state_reason':'completed'})
after=api('issue144-after',f'repos/{REPO}/issues/144')
check('completed closure independently read back',after['state']==closed['state']=='closed' and after['state_reason']==closed['state_reason']=='completed' and after['closed_at'])
check('original issue body title author creation and labels unchanged after closure',all(after[k]==before[k] for k in ['body','title','created_at']) and after['user']==before['user'] and after['labels']==before['labels'])
save('CLOSURE414.json',{'issue':144,'state':after['state'],'state_reason':after['state_reason'],'closed_at':after['closed_at'],'comment_id':comment['id'],'comment_url':comment['html_url'],'original_metadata_preserved':True,'before_sha256':sha((OUT/'issue144-reconciled-before.response.json').read_bytes()),'after_sha256':sha((OUT/'issue144-after.response.json').read_bytes()),'criterion_review_sha256':sha((OUT/'ACCEPTANCE414.json').read_bytes()),'native_or_build_replays':0,'release_allowed':False})
pages=api('all-issues-after',f'repos/{REPO}/issues?state=all&per_page=100',paginate=True)
issues=[x for page in pages for x in page if 'pull_request' not in x]
check('complete current issue172 read after closure',len(issues)==172 and len({x['number'] for x in issues})==172)
counts={state:sum(x['state']==state for x in issues) for state in ['closed','open']};counts['total']=len(issues)
save('COUNTS414.json',{'counts':counts,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_issues_response_sha256':sha((OUT/'all-issues-after.response.json').read_bytes()),'states':[{'number':x['number'],'state':x['state'],'state_reason':x['state_reason'],'title':x['title'],'body_sha256':sha((x.get('body') or '').encode()),'labels':sorted(l['name'] for l in x['labels']),'author':x['user']['login'],'created_at':x['created_at']} for x in sorted(issues,key=lambda x:x['number'])]})
print(json.dumps({'closed_issue':144,'closure':after['closed_at'],'comment':comment['html_url'],'counts':counts,'passive_review_checks':len(checks),'native_replays':0}))
