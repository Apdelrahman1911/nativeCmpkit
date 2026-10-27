"""Additive XML timestamp and available-marker-scope readback; no tests execute."""
from pathlib import Path
import datetime as dt,hashlib,json,shutil,zipfile,xml.etree.ElementTree as ET
TMP=Path(__file__).parent;OUT=TMP/'review-archive'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1);assert sha(OUT/name)==digest,name
run=json.loads((OUT/'lead-independent-review.json').read_text());assert run['run_id']==40507836194 and run['evidence_integrity_passed']
assert run['actual_consumer_methods_verified']==7 and run['actual_xml_reports']==2
with zipfile.ZipFile(OUT/'raw/12736236898.zip') as z:
 receipt=json.loads(z.read('ci-consumer/core-io-desktop/receipt.json'));observed=[]
 for name in z.namelist():
  if not name.endswith('.xml'):continue
  payload=z.read(name);assert b'<!DOCTYPE' not in payload and b'<!ENTITY' not in payload
  root=ET.fromstring(payload);stamp=root.attrib['timestamp'];parsed=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
  assert parsed.utcoffset() is not None
  ns=int(parsed.timestamp()*1_000_000_000)
  assert receipt['consumer_started_ns']-2_000_000_000 <= ns <= receipt['consumer_ended_ns']+2_000_000_000
  observed.append({'path':name,'sha256':hashlib.sha256(payload).hexdigest(),'reported_testsuite_timestamp':stamp,'within_actual_consumer_execution_window':True})
 assert len(observed)==2
record={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':run['source_revision'],'run_id':run['run_id'],'original_archive_hashes_unchanged':True,'actual_XML_timestamps_verified':observed,
 'raw_child_producer_consumer_logs_uploaded':False,'raw_marker_counters_independently_recounted':False,'source_enforced_exactly_one_test_marker_and_reported_marker_reviewed':True,
 'owning_resolution_to_runtime_origin_property_source_reviewed':True,'loaded_JAR_hashes_directly_read_by_passed_real_test_not_by_local_reviewer':True,'new_library_native_or_consumer_methods_executed_by_this_addendum':0,'release_readiness_certified':False,
 'limits':'Original Gradle resolution bytes and candidate JARs are not uploaded; source-bound real builder assertions and parsed exact hash bindings, not local re-reading of those payloads. Both original raw XML reports are independently recounted/hashed and timestamps checked. Successful child logs are captured by the controller, not forwarded into the complete workflow console. The first reviewer red from that incorrect console assumption is preserved separately; no runtime failure is invented or hidden.'}
with (OUT/'fresh-XML-source-scope-addendum.json').open('x') as f:json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
for name in ['review-addendum.py','reviewer-red001.json','reviewer-red001.py']:shutil.copyfile(TMP/name,OUT/name)
extra=['fresh-XML-source-scope-addendum.json','review-addendum.py','reviewer-red001.json','reviewer-red001.py']
(OUT/'ADDENDUM-SHA256SUMS').write_text(''.join(sha(OUT/n)+'  '+n+'\n' for n in sorted(extra)))
print(json.dumps({'passed':True,'run_id':run['run_id'],'raw_XML_reports':len(observed),'new_runtime_methods':0,'original_archive_unchanged':True},indent=2))
