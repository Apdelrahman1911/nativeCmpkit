"""Original NAV-003/PERM-023 scope acceptance, not unrelated release clearance."""
from pathlib import Path
import datetime as dt, hashlib, json, shutil, subprocess
ROOT=Path('/root/projects/nativeCmpKit')
BASE=Path(__file__).parent
OUT=ROOT/'docs/development/evidence/navgeo-original-acceptance-20261027'
SOURCE=Path('/dev/shm/nativecmpkit-original-acceptance-20261027-003')
REV='769bf7dea1ca69ac23ef74d7f7140303b130657a'
RUN_REVIEW='docs/development/evidence/github-actions/40528445496/lead-independent-review.json'
FINDINGS={'NAV-003':('NAV.json',91,'navigation.NavArgumentAndBundleTest'),
          'PERM-023':('PERM-geo.json',156,'geo.LatLngTest')}
METHODS={'NAV-003':[
 ['typedRequiredArgumentHasNoDefault','everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference'],
 ['nullableDefaultDistinguishesExplicitNullFromAbsence','everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference'],
 ['invalidDefaultsFailAtConstruction','everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference'],
 ['everyBuiltInDefaultIsValidatedAndRoundTripsInBundle','everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference','nullableArrayDefaultsAndDefensiveCopies','checkedAccessDoesNotCoerceOrThrowForWrongScalarType']],
 'PERM-023':[
 ['sphericalDistanceUnitsAndIdenticalPoints','datelineUsesShortArc','identicalPolesDoNotDependOnLongitude','antipodalDistanceIsFiniteAndUndefinedBearingIsExplicit','cardinalBearingsUseTrueNorthClockwiseConvention','tinyDistinctCoordinatesAreNotRoundedIntoIdenticalPoints','validatedFactoryRejectsInvalidDomains','longitudeNormalizationIsExplicitAndDoesNotFoldInvalidLatitude'],
 ['seededDistancesAreSymmetricBoundedAndFiniteAcrossTargets','compatibilityBearingDefaultRoundsAndWrapsToZeroNot360']]}
def sha(raw):return hashlib.sha256(raw).hexdigest()
assert not OUT.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==REV
run=json.loads((ROOT/RUN_REVIEW).read_bytes())
assert run['evidence_integrity_passed'] and run['source_revision']==REV and run['actual_executions']==321
assert {r['suite'] for r in run['four_runtime_results']}=={'desktop','js','wasm','ios'}
baselines={x['id']:x for f in (ROOT/'docs/audit/findings').glob('*.json') for x in json.loads(f.read_bytes())}
records=[]
for fid,(filename,number,cls) in FINDINGS.items():
 original=baselines[fid]
 issue=json.loads((SOURCE/f'issue-{number}-before.json').read_bytes())
 assert issue['state']=='open' and issue['number']==number and 'pull_request' not in issue
 assert f'<!-- nativecmpkit-item:audit:{fid} -->' in issue['body']
 requirements=issue['body'].split('## Required tests / acceptance criteria\n',1)[1].split('\n## Dependencies',1)[0].strip().splitlines()
 assert requirements==['- '+r for r in original['required_tests']]
 assert len(METHODS[fid])==len(original['required_tests'])
 ledger_path='docs/development/resolutions/'+filename
 ledger=json.loads((ROOT/ledger_path).read_bytes())
 disposition=next(r for r in ledger if r['id']==fid)
 rows=[]
 for requirement,methods in zip(original['required_tests'],METHODS[fid]):
  executed=[]
  for result in run['four_runtime_results']:
   cases=result['original_acceptance_class_methods'][cls]
   for method in methods:
    found=[case for case in cases if case['name'].split('[',1)[0]==method]
    assert len(found)==1 and found[0]['status']=='passed'
    executed.append({'suite':result['suite'],'slot':result['slot'],'method':method,'classname':found[0]['classname'],
                     'XML_method_name':found[0]['name'],'job_url':result['job_url']})
  rows.append({'requirement':requirement,'status':'passed-original-scope-on-four-runtimes','executed_methods':executed})
 records.append({'id':fid,'issue_number':number,'issue_url':issue['html_url'],'original_finding_priority':original['priority'],
                 'original_dependencies':original['dependencies'],'original_required_tests':original['required_tests'],
                 'issue_body_sha256_before':sha(issue['body'].encode()),'issue_title_sha256_before':sha(issue['title'].encode()),
                 'issue_labels_before':sorted(l['name'] for l in issue['labels']),
                 'previous_status':disposition['status'],'previous_remaining_preserved_verbatim':disposition['remaining'],
                 'requirements_review':rows,'accepted_for_original_scoped_closure':True,
                 'limits_preserved_outside_this_specific_original_defect':run['limits'],
                 'compatibility':disposition['compatibility']})
OUT.mkdir()
for _,number,_ in FINDINGS.values():
 for ext in ['json','stderr']:
  name=f'issue-{number}-before.{ext}'
  shutil.copyfile(SOURCE/name,OUT/name)
shutil.copyfile(Path(__file__),OUT/'review-required-tests.py')
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_integrity_passed':True,'source_revision':REV,
        'immutable_runtime_revision':REV,'immutable_run_id':40528445496,'immutable_run_review':RUN_REVIEW,
        'findings_accepted_for_scoped_closure':records,'owning_current_input_hashes_identical_to_runtime':run['reviewed_current_NAV_GEO_source_hashes'],
        'actual_target_executions':321,'actual_XML_reports':32,'original_baseline_modified':False,
        'issues_mutated':False,'publication_performed':False,'release_readiness_certified':False,
        'scope':'All original NAV-003 and PERM-023 requirements mapped to reviewed actual four-runtime named methods. Previous remaining prose preserved verbatim; unrelated whole-module/device/ABI/consumer/legal/dependency/profiling gates remain separate, not waived.'}
(OUT/'lead-original-acceptance-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(OUT/'README.md').write_text('# NAV-003 / PERM-023 original acceptance\n\nEach original requirement is matched to named fresh JVM/JS/Wasm/iOS-simulator methods at immutable `'+REV+'`. Review the run archive and `lead-original-acceptance-review.json`; this does not close an issue until additive evidence is pushed and a state-only closure is exactly read back. Previous remaining observations and issue bodies are preserved; full-module/release gates remain separate.\n')
(OUT/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'accepted_ids':list(FINDINGS),'issues_closed':0,'archive':str(OUT)},indent=2))
