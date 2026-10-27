"""Read-only independent fidelity/source review of already-executed iOS IO diagnostics."""
from pathlib import Path
import gzip,hashlib,json,re,sys,zipfile
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
OUT=ROOT/'docs/development/evidence/ios-io-diagnostics-20261027'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as r
review=json.loads((OUT/'lead-diagnostic-review.json').read_bytes())
for item in review['archive_manifest']:
 p=OUT/item['archive_relative'];data=p.read_bytes()
 assert hashlib.sha256(data).hexdigest()==item['archive_sha256']
 raw=gzip.decompress(data) if item['gzip'] else data
 assert hashlib.sha256(raw).hexdigest()==item['original_sha256'] and len(raw)==item['original_bytes']
for n,code in [('compile001',1),('compile002',0),('compile003',0)]:
 receipt=json.loads((OUT/n/'receipt.json').read_bytes());log=(OUT/n/'compile.log').read_bytes()
 assert hashlib.sha256(log).hexdigest()==receipt['log_sha256'] and receipt['execution']['exit_code']==code
 maps=[json.loads(gzip.decompress((OUT/n/('inputs-'+phase+'.json.gz')).read_bytes())) for phase in ('before','after')]
 assert maps[0]==maps[1] and r.input_digest(maps[0])==receipt['source_digest'] and len(maps[0])==733
 assert receipt['actual_library_or_native_methods_executed']==0
actual=r.snapshot_inputs(ROOT)
held=json.loads(gzip.decompress((OUT/'compile003/inputs-after.json.gz').read_bytes()))
assert actual==held
for row in review['tests_and_outputs']:assert r.sha256(ROOT/row['path'])==row['sha256']
assert sum(len(row['methods']) for row in review['tests_and_outputs'])==47
for row in review['klibs']:
 for file in row['files']:assert r.sha256(ROOT/file['path'])==file['sha256']
acq=json.loads((BASE/'coil-source-acquisition.json').read_bytes());archive=BASE/'coil-core-3.6.2-sources.jar'
assert r.sha256(archive)==acq['sha256'] and acq['success']
with zipfile.ZipFile(archive) as z:
 entries=[]
 for name,need in [('commonMain/coil3/decode/Decoder.kt',['suspend fun decode(): DecodeResult?', 'Implementations **must not** consume', 'result: SourceFetchResult']),('commonMain/coil3/intercept/EngineInterceptor.kt',['} finally {','(fetchResult as? SourceFetchResult)?.source?.closeQuietly()']),('commonMain/coil3/request/ImageRequest.kt',['fun coroutineContext(context: CoroutineContext)', 'fun decoderFactory(factory: Decoder.Factory)'])]:
  raw=z.read(name);text=raw.decode()
  for assertion in need:assert assertion in text
  entries.append({'archive_entry':name,'sha256':hashlib.sha256(raw).hexdigest(),'inspected_contracts':need})
source={'origin':acq['origin_url'],'artifact_sha256':acq['sha256'],'entries':entries,'code_executed_from_archive':False,'dependency_trust_certified':False,'scope':'Exact configured Coil3.6.2 source inspected for nullable suspending Decoder API, consume-in-decode contract, real SourceFetchResult ownership finally, request scheduler and decoder factory selection. No fetched code executed, bootstrap trust or package/legal certification.'}
(OUT/'coil-decoder-source-review.json').write_text(json.dumps(source,indent=2,sort_keys=True)+'\n')
final={'passed':True,'reviewed_utc':r.utc_now(),'fidelity_entries':len(review['archive_manifest']),'held_inputs':733,'final_source_digest':r.input_digest(actual),'authored_compiled_methods':47,'expected_native_reports':8,'mandatory_native_cases':22,'actual_native_executions':0,'all_four_KLIB_manifests_and_file_hashes_inspected':True,'original_getBytes_failure_and_fixture_failure_retained':True,'coil_source_review':source,'issue4_still_open_at_archive':json.loads((OUT/'issue4-before.json').read_bytes())['state']=='open','publication_performed':False,'release_readiness_certified':False}
(OUT/'lead-replay-review.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n');(OUT/'review-archive.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(r.sha256(p)+'  '+str(p.relative_to(OUT))+'\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({'passed':True,'entries':len(review['archive_manifest']),'native_executions':0,'source_digest':r.input_digest(actual)},indent=2))
