"""Accept every original NAV-005 criterion; do not close unrelated NAV-004."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
OUT = BASE / 'archive'
DEST = ROOT / 'docs/development/evidence/navcodec-original-acceptance-20261027'
REV = '70114ff3d579af291c4a3028181efc7d884e23a9'
PRIOR = '769bf7dea1ca69ac23ef74d7f7140303b130657a'
REPO = 'Apdelrahman1911/nativeCmpkit'
PRIOR_REVIEW = 'docs/development/evidence/github-actions/40528445496/lead-independent-review.json'
DESKTOP_REVIEW = 'docs/development/evidence/github-actions/40549350671/lead-independent-review.json'
assert not OUT.exists() and not DEST.exists()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
OUT.mkdir()
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

original = next(x for x in json.loads((ROOT / 'docs/audit/findings/NAV.json').read_bytes()) if x['id'] == 'NAV-005')
prior = json.loads((ROOT / PRIOR_REVIEW).read_bytes())
desktop = json.loads((ROOT / DESKTOP_REVIEW).read_bytes())
assert prior['evidence_integrity_passed'] and prior['source_revision'] == PRIOR
assert desktop['evidence_integrity_passed'] and desktop['source_revision'] == REV
assert desktop['totals']['tests'] == desktop['totals']['passed'] == 54 and desktop['actual_xml_reports'] == 7
assert desktop['all_previous_52_desktop_case_identities_retained']
old_issue_path = Path('/dev/shm/nativecmpkit-navcodec-original-acceptance-20261027/issue-93-before.json')
old_issue = json.loads(old_issue_path.read_bytes())
command = ['gh', 'api', 'repos/' + REPO + '/issues/93']
result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
(OUT / 'issue-93-current-before.json').write_bytes(result.stdout)
(OUT / 'issue-93-current-before.stderr').write_bytes(result.stderr)
assert result.returncode == 0, 'Read-only observation failed; no automatic retry'
issue = json.loads(result.stdout)
assert issue['number'] == 93 and issue['state'] == 'open' and 'pull_request' not in issue
for key in ('title', 'body', 'labels'):
    assert issue[key] == old_issue[key]
assert '<!-- nativecmpkit-item:audit:NAV-005 -->' in issue['body']
requirements = issue['body'].split('## Required tests / acceptance criteria\n', 1)[1].split('\n## Dependencies', 1)[0].strip().splitlines()
assert requirements == ['- ' + text for text in original['required_tests']] and len(requirements) == 4

owning = {name: digest for name, digest in desktop['reviewed_current_navigation_source_hashes'].items()
          if name.startswith('calf-navigation/src/commonMain/') or name.endswith('AdaptiveNavTypeCodecTest.kt')}
assert owning and all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in owning.items())
assert all(prior['reviewed_current_NAV_GEO_source_hashes'][name] == digest for name, digest in owning.items())
four_codec = []
for row in prior['four_runtime_results']:
    path = ROOT / f"docs/development/evidence/github-actions/40528445496/raw/{row['artifact_id']}.zip"
    assert 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest() == row['artifact_digest']
    with zipfile.ZipFile(path) as archive:
        xmls = [name for name in archive.namelist() if name.startswith('calf-navigation/') and name.endswith('AdaptiveNavTypeCodecTest.xml')]
        assert len(xmls) == 1
        cases = lt.junit_cases(archive.read(xmls[0]))
        assert len(cases) == 10 and all(case['status'] == 'passed' for case in cases)
        assert {case['name'].split('[', 1)[0] for case in cases} == set(desktop['actual_source_methods']['AdaptiveNavTypeCodecTest'])
        four_codec.append({'suite': row['suite'], 'slot': row['slot'], 'run_id': prior['run_id'],
                           'revision': PRIOR, 'job_url': row['job_url'], 'XML': xmls[0],
                           'XML_sha256': hashlib.sha256(archive.read(xmls[0])).hexdigest(), 'cases': cases})
assert {row['suite'] for row in four_codec} == {'desktop', 'js', 'wasm', 'ios'}
methods_by_criterion = [
    ['stringArrayInferenceIncludesEmptyAndRejectsMixedValues'],
    ['stringsRoundTripNullLiteralDelimitersAndUnicode', 'primitiveArraysRoundTripNullEmptyAndValues',
     'stringArrayFramingDistinguishesAllEmptyAndLiteralCases', 'floatScalarRoundTripsSignedZeroAndSpecialValues',
     'floatArrayRoundTripsSignedZeroAndSpecialValues'],
    ['builtInNameResolutionAndScalarCodecsAreTruthful'],
]
rows = []
for requirement, methods in zip(original['required_tests'][:3], methods_by_criterion):
    executed = []
    for runtime in four_codec:
        for method in methods:
            found = [case for case in runtime['cases'] if case['name'].split('[', 1)[0] == method]
            assert len(found) == 1 and found[0]['status'] == 'passed'
            executed.append({key: runtime[key] for key in ('suite', 'slot', 'run_id', 'revision', 'job_url', 'XML', 'XML_sha256')}
                            | {'method': method, 'actual_case': found[0]})
    rows.append({'requirement': requirement, 'status': 'passed-original-scope-four-runtime', 'executed_methods': executed})
work_methods = desktop['actual_source_methods']['NavArrayParsingWorkTest']
executed = []
for method in work_methods:
    found = [case for case in desktop['actual_cases'] if case['classname'] == 'com.mohamedrejeb.calf.navigation.NavArrayParsingWorkTest'
             and case['name'] == method + '[desktop]']
    assert len(found) == 1 and found[0]['status'] == 'passed'
    executed.append({'suite': 'desktop', 'slot': 'desktop-linux-x64', 'run_id': desktop['run_id'], 'revision': REV,
                     'job_url': desktop['job_url'], 'method': method, 'actual_case': found[0]})
assert len(executed) == 2 and len(desktop['allocation_probe_rows']) == 12
rows.append({'requirement': original['required_tests'][3], 'status': 'passed-original-scope-bounded-real-JVM-work-allocation',
             'executed_methods': executed, 'actual_allocation_rows': desktop['allocation_probe_rows'],
             'interpretation': 'Five array APIs read every tested element once at0/1/16/256/4096. '
                 'Twelve finite Int-array allocated-byte comparisons at128/512/2048/4096 preserve outputs and restore the management flag; '
                 'no wall-clock success thresholds. Legacy append remains copying/quadratic and is not adopted as a large-external-input parser. '
                 'Use additive bulk parseValues for such data; this is not a portable latency/peak-heap/Native-performance guarantee or new external-input bound.'})
ledger = json.loads((ROOT / 'docs/development/resolutions/NAV.json').read_bytes())
disposition = next(row for row in ledger if row['id'] == 'NAV-005')
erased = next(row for row in ledger if row['id'] == 'NAV-004')
assert erased['status'] != 'verified'
source = (ROOT / 'calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt').read_text()
assert all(token in source for token in ('fun parseSerializedValue', 'fun parseValues', 'getStringArray', 'Unsupported navigation type'))
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence_integrity_passed': True,
    'source_revision': REV, 'immutable_work_run_id': desktop['run_id'], 'immutable_codec_run_id': prior['run_id'],
    'finding': 'NAV-005', 'issue_number': 93, 'issue_url': issue['html_url'],
    'original_priority': original['priority'], 'original_dependencies': original['dependencies'],
    'dependency_scope_review': 'NAV-003 is verified/closed. NAV-004 remains independently open for legacy erased get<T>; '
        'current codecs use typed/checked access and do not depend on certifying arbitrary erased legacy reads. No NAV-004 requirement is waived.',
    'original_required_tests': original['required_tests'], 'requirements_review': rows,
    'issue_body_sha256_before': hashlib.sha256(issue['body'].encode()).hexdigest(), 'issue_title_before': issue['title'],
    'issue_labels_before': sorted(label['name'] for label in issue['labels']),
    'previous_status': disposition['status'], 'previous_remaining_preserved_verbatim': disposition['remaining'],
    'owning_codec_source_hashes_identical_to_both_revisions': owning,
    'current_navigation_source_hashes_identical_to_work_run': desktop['reviewed_current_navigation_source_hashes'],
    'accepted_for_original_scoped_closure': True, 'remaining_original_acceptance_requirements': [],
    'compatibility': disposition['compatibility'], 'independent_limits': desktop['limits'],
    'issues_mutated': False, 'publication_performed': False, 'release_readiness_certified': False,
    'scope': 'Every original NAV-005 criterion accepted from exact unchanged four-runtime codec sources plus immutable real JVM work/allocation. '
        'Push acceptance and current source/stage evidence before a separate state-only issue closure. Unrelated legacy getter/native/device/consumer/ABI/legal/dependency gates remain.'}
shutil.copyfile(old_issue_path, OUT / 'issue-93-original-before.json')
shutil.copyfile(Path(__file__), OUT / 'review.py')
(OUT / 'lead-original-acceptance-review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
(OUT / 'README.md').write_text('# NAV-005 original acceptance\n\n'
    'All four original requirements are mapped to named actual library methods: unchanged codec/inference/type-resolution '
    'on JVM/JS/Wasm/iOS simulator, plus the new immutable finite JVM work/allocation probes. '
    'NAV-004 remains independently open; no arbitrary erased-getter, Native-performance, external-input-limit or release clearance. '
    'Issue closure requires pushed evidence and exact additive-comment/state-only readback.\n')
(OUT / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n'
                                    for path in sorted(OUT.iterdir()) if path.is_file()))
shutil.copytree(OUT, DEST)
assert all(path.read_bytes() == (DEST / path.relative_to(OUT)).read_bytes() for path in OUT.rglob('*') if path.is_file())
print(json.dumps({'passed': True, 'accepted_finding': 'NAV-005', 'original_criteria': len(rows),
                  'new_immutable_work_methods': len(executed), 'issues_closed': 0, 'archive': str(DEST)}, indent=2))
