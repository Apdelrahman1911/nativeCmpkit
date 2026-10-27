"""Review actual bounded navigation work/allocation evidence; preserve both compiler failures."""
from pathlib import Path
import datetime as dt,hashlib,json,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path('/dev/shm')
OUT=ROOT/'docs/development/evidence/navigation-array-work-20261027'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
F='calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/NavArrayParsingWorkTest.kt'
A=[BASE/f'nativecmpkit-nav-array-work-20261027-{n:03d}' for n in (1,2,3)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def instant(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
assert not OUT.exists()
current=lt.snapshot_inputs(ROOT);assert len(current)==726
runs=[]
for number,out in enumerate(A,1):
 before=load(out/'inputs-before.json');after=load(out/'inputs-after.json')
 assert before==after==load(out/'copied-inputs-before.json')==load(out/'copied-inputs-after.json') and len(before)==726
 execution=load(out/'execution-before-report-review.json')
 assert execution['execution']['exit_code']==(0 if number==3 else 1) and not execution['execution'].get('stop_reason')
 log=(out/'test.log').read_text()
 if number<3:
  review=load(out/'lead-failed-review.json')
  assert ':calf-navigation:compileTestKotlinDesktop FAILED' in log and not lt.execution_markers(out/'test.log')
  assert "NavArrayParsingWorkTest.kt:" in log
  runs.append({'attempt':number,'execution':execution['execution'],'executed_testcases':0,'failure_stage':'New fixture Kotlin compile; no library execution','inputs_held':True,'selected_inputs':726,'fixture_sha256':sha(out/'fixture-before.kt'),'log_sha256':sha(out/'test.log')})
 else:
  receipt=load(out/'receipt.json');assert before==current
  assert receipt['passed'] and receipt['inputs_held'] and receipt['selected_input_count']==726
  assert receipt['source_revision']==lt.git_revision(ROOT) and receipt['dirty_held_worktree']
  assert receipt['inputs_sha256']==lt.input_digest(current) and receipt['log_sha256']==sha(out/'test.log')
  assert receipt['driver_sha256']==sha(out/'driver.py')
  assert receipt['java_executable_sha256']==sha(Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java'))
  assert 'OpenJDK 64-Bit Server VM' in receipt['java_version'] and 'version "17.' in receipt['java_version']
  assert lt.execution_markers(out/'test.log')=={':calf-navigation:desktopTest':1}
  module=receipt['module'];assert len(module['reports'])==1
  p=out/'reports'/module['reports'][0]['path'];payload=p.read_bytes();assert sha(p)==module['reports'][0]['sha256']
  cases=lt.junit_cases(payload);assert lt.case_counts(cases)=={k:module[k] for k in lt.case_counts(cases)}
  assert len(cases)==2 and {c['name'] for c in cases}=={'boundedIntArrayProbeRecordsActualAllocationWithoutTimingAssertions[desktop]','bulkParsersReadEachBoundedInputOnceForEveryBuiltInArray[desktop]'}
  assert all(c['classname']=='com.mohamedrejeb.calf.navigation.NavArrayParsingWorkTest' and c['status']=='passed' for c in cases)
  xml=ET.fromstring(payload,parser=ET.XMLParser(target=lt.NoDtdBuilder()))
  assert instant(receipt['started_utc'])<=instant(xml.attrib['timestamp'])<=instant(receipt['finished_utc'])
  assert not list(xml.iter('failure')) and not list(xml.iter('error')) and not list(xml.iter('skipped'))
  printed=''.join(x.text or '' for x in xml.iter('system-out'))
  rows=[json.loads(line.removeprefix('nativecmpkit-nav-array-probe:')) for line in printed.splitlines() if line.startswith('nativecmpkit-nav-array-probe:')]
  assert len(rows)==12 and [(r['elements'],r['trial']) for r in rows]==[(n,t) for n in (128,512,2048,4096) for t in range(3)]
  assert all(set(r)=={'elements','trial','bulk_bytes','legacy_bytes','bulk_ns','legacy_ns'} and all(type(v) is int and v>=0 for v in r.values()) for r in rows)
  assert all(r['legacy_bytes']>r['bulk_bytes']>0 for r in rows if r['elements']==4096)
  runs.append({'attempt':3,'execution':execution['execution'],'executed_testcases':2,'passed':True,'XML_reports':1,'XML_timestamp':xml.attrib['timestamp'],'XML_sha256':sha(p),'inputs_held':True,'selected_inputs':726,'testcases':cases,'measurements':rows,'log_sha256':sha(out/'test.log'),'java_version':receipt['java_version']})
s1=(A[0]/'fixture-before.kt').read_text();s2=(A[1]/'fixture-before.kt').read_text();s3=(ROOT/F).read_text()
assert s1.replace('val result = AdaptiveNavType.StringArrayType.parseValues(source)','val result = requireNotNull(AdaptiveNavType.StringArrayType.parseValues(source))')==s2
assert s2.replace('val bulk = observe(bean, thread) { AdaptiveNavType.IntArrayType.parseValues(values) }','val bulk = observe(bean, thread) { requireNotNull(AdaptiveNavType.IntArrayType.parseValues(values)) }')==s3
for marker in ('isThreadAllocatedMemorySupported','isThreadAllocatedMemoryEnabled = previouslyEnabled','finally {','assertContentEquals(expected, bulk.result)','assertContentEquals(expected, legacy.result)','if (size == 4096) assertTrue(legacy.bytes > bulk.bytes)','for (size in listOf(0, 1, 16, 256, 4096))','assertContentEquals(IntArray(values.size) { 1 }, source.reads)'):
 assert marker in s3
assert 'assertTrue(bulk.nanos' not in s3 and 'assertTrue(legacy.nanos' not in s3
# Review log for accidental credential material; never export environment/property dumps.
for out in A:
 log=(out/'test.log').read_bytes()
 assert not any(re.search(p,log) for p in (br'(?i)authorization:\s*(bearer|basic)',br'gh[pousr]_[A-Za-z0-9]{20,}',br'github_pat_[A-Za-z0-9_]{20,}',br'-----BEGIN .*PRIVATE KEY-----'))
OUT.mkdir()
for number,out in enumerate(A,1):
 target=OUT/f'attempt-{number:03d}';target.mkdir()
 for name in ('driver.py','execution-before-report-review.json','inputs-before.json','inputs-after.json','copied-inputs-before.json','copied-inputs-after.json','test.log'):
  shutil.copyfile(out/name,target/name)
 for name in ('fixture-before.kt','lead-failed-review.json','collector.json','receipt.json'):
  if (out/name).exists():shutil.copyfile(out/name,target/name)
 if (out/'reports').exists():shutil.copytree(out/'reports',target/'reports')
shutil.copyfile(ROOT/F,OUT/'fixture-verified.kt');shutil.copyfile(Path(__file__),OUT/'lead-review.py')
review={'reviewed_utc':lt.utc_now(),'evidence_integrity_passed':True,'source_revision':lt.git_revision(ROOT),'dirty_held_worktree':True,'selected_inputs':726,'current_inputs_sha256':lt.input_digest(current),'runs':runs,'all_source_and_copied_inputs_held_per_attempt':True,'only_two_explicit_nullable_fixture_repairs_between_runs':True,'actual_fresh_methods':2,'actual_fresh_XML_reports':1,'actual_measurement_rows':12,'timing_assertions':False,'required_real_JDK_management_counter':True,'counter_flag_restoration_contract':'finally restores the original flag; method completes with no skip/failure. No other global VM management configuration changed.','bounded_read_scope':{'array_types':5,'input_sizes':[0,1,16,256,4096],'reads_per_element':1},'allocation_scope':{'array_type':'IntArray','input_sizes':[128,512,2048,4096],'trials_per_size':3,'comparison':'Actual JVM thread allocated bytes; bulk parseValues versus legacy repeated parseValue(previous). Both actual contents asserted; only a strict larger legacy allocation at4096 is required.','observed_4096_bulk_bytes':[r['bulk_bytes'] for r in rows if r['elements']==4096],'observed_4096_legacy_bytes':[r['legacy_bytes'] for r in rows if r['elements']==4096]},'limits':['Two held dirty-source JVM methods, not an immutable candidate or Apple/browser/device benchmark.','No external-input acceptance limit, general latency/peak-memory guarantee, leak/sanitizer/profiling certification or large-input legacy adoption is established.','Elapsed measurements are observations only; no wall-clock ratios or budgets determine success.','First two compiler failures and downstream collector errors remain evidence, not runtime tests.','Immutable desktop execution and original issue acceptance/pushed evidence/readback are still required before closure.'],'issues_closed':0,'publication_performed':False,'release_readiness_certified':False}
(OUT/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(OUT/'README.md').write_text('# Bounded navigation parsing work/allocation evidence\n\nTwo actual library JVM methods pass after two preserved nullable-fixture compiler failures. Review `lead-independent-review.json` for fresh XML, held726 source/copy inputs and12 actual thread-allocation rows. Five array parsers read each bounded input once; legacy incremental append still copies and is not recommended for large external inputs. This is a finite dirty-source diagnostic, not immutable/native/consumer/release certification or a general performance guarantee.\n')
(OUT/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({'passed':True,'actual_methods':2,'fresh_XML':1,'measurement_rows':12,'preserved_compile_failures':2,'immutable_or_release_certified':False,'archive':str(OUT)},indent=2))
