"""One-time read-only archive/raw-output comparison. Does not run tests or Gradle."""
from pathlib import Path
import json
import hashlib
import datetime as dt
import re
import xml.etree.ElementTree as ET

ROOT = Path('/root/projects/nativeCmpKit')
BASE = '94d2492e99d5cbc060409d94d9f88febd06222d5'
OWNED = ('calf-io/', 'calf-file-picker/', 'calf-file-picker-coil/')
PIN = {
    'wasm-full-004': 'cebd13be6af5d0b4fe60a7d034eb86ebadbbd0aff66b5a271438e4ae9d1a6229',
    'js-full-004': '256d0264ce3ff30cb34f956258af3c8c2ae39237f8c7d625ff1ee47887cee72e',
    'io-nav-desktop-001': 'ebb66c624218d6336e293d1229e5d635a238d370567c08459ff2e04cb9b1ae1e',
}
CTX = {
    'wasm-full-004': '8de4f671600a3fc6c96e3824e574dd3291a9a675fdb7b1032c09d2a6bda15040',
    'js-full-004': '119c6063462cd324d1e61e0f611c36f251aea8ba839486110b0aef1691f09d8d',
    'io-nav-desktop-001': 'd5975eab3d9a854e40c2931bed2949f07d8622e5835b5d45700f447b896402cd',
}


def path(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def sha(p):
    h = hashlib.sha256()
    with path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(path(p).read_text())


def stamp(s):
    return dt.datetime.fromisoformat(s).timestamp()


def canon(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def digest(v):
    return hashlib.sha256(''.join(f'{h}  {p}\n' for p, h in sorted(v.items())).encode()).hexdigest()


def manifest(d):
    p = d / 'SHA256SUMS'
    items = {}
    for line in p.read_text().splitlines():
        h, rel = line.split('  ', 1)
        assert re.fullmatch('[0-9a-f]{64}', h)
        q = d / rel
        assert q.resolve().is_relative_to(d.resolve()) and not q.is_symlink() and rel not in items
        assert sha(q) == h, (q, 'manifest mismatch')
        items[rel] = h
    actual = {str(p.relative_to(d)) for p in d.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'}
    assert actual == set(items), (d, 'manifest completeness')
    return {'path': str(p.relative_to(ROOT)), 'sha256': sha(p), 'entries_checked': len(items)}


def cases(p):
    root = ET.parse(path(p)).getroot()
    out = []
    for x in root.iter('testcase'):
        states = [k for k in ('failure', 'error', 'skipped') if x.find(k) is not None]
        assert len(states) <= 1
        state = {'failure': 'failed', 'error': 'error', 'skipped': 'skipped'}[states[0]] if states else 'passed'
        out.append({'classname': x.attrib['classname'], 'name': x.attrib['name'], 'status': state})
    assert int(root.attrib['tests']) == len(out)
    for key, state in [('failures', 'failed'), ('errors', 'error'), ('skipped', 'skipped')]:
        assert int(root.attrib.get(key, 0)) == sum(x['status'] == state for x in out)
    return sorted(out, key=lambda x: (x['classname'], x['name'], x['status']))


def normcase(x):
    return (x['classname'].split('.')[-1], x['name'].split('[', 1)[0], x['status'])


def review_runs():
    results = {}
    all_inputs = []
    for name in PIN:
        d = ROOT / 'docs/development/evidence' / name
        a = read(d / 'archive.json')
        r = read(d / 'receipt.json')
        plan = read(d / 'plan.json')
        runtime = read(d / 'runtime.json')
        assert sha(d / 'archive.json') == PIN[name]
        mani = manifest(d)
        assert a['passed'] and r['passed'] and a['execution'] == r['execution'] and a['execution']['exit_code'] == 0
        assert a['source_revision'] == r['source_revision'] == r['source_revision_after'] == runtime['source_revision'] == BASE
        assert a['source_tree_dirty'] and r['source_tree_dirty'] and runtime['source_tree_dirty']
        assert a['command'] == r['command'] and a['started_utc'] == r['started_at_utc'] and a['finished_utc'] == r['finished_at_utc']
        assert not a['errors'] and not a['failure_details'] and not r['changed_inputs'] and not r['errors']
        assert sha(d / 'receipt.json') == a['producer_receipt_sha256']
        assert sha(d / 'runtime.json') == r['runtime_receipt_sha256']
        for pair in a['archives']:
            assert sha(pair['source']) == sha(pair['archive']) == pair['sha256'], pair
        assert sha(a['raw_log']['path']) == a['raw_log']['sha256']
        assert sha(d / 'gradle.sanitized.log') == a['sanitized_log_sha256']
        assert sha(d / 'collector.py') == a['collector_sha256']
        before = read(d / 'inputs-before.json')
        after = read(d / 'inputs-after.json')
        assert before == after and len(before) == 693
        assert len(before) == a['selected_input_count'] and a['selected_inputs_unchanged']
        # Helper inputs_*_sha256 is the sorted hash/path digest, not raw JSON.
        assert sha(d / 'inputs-before.json') == sha(d / 'inputs-after.json') == 'd2e86ceb7dc4fb858dc759ed3c0ab35e33b85ff813790302963d9d0fefbd0b73'
        assert digest(before) == r['inputs_before_sha256'] == r['inputs_after_sha256']
        current_changes = [p for p, h in after.items() if sha(p) != h]
        assert not current_changes, current_changes
        owned = {p: h for p, h in after.items() if p.startswith(OWNED)}
        assert len(owned) == 165
        all_inputs.append(before)
        lines = (d / 'gradle.sanitized.log').read_text().splitlines()
        start = stamp(a['started_utc'])
        end = stamp(a['finished_utc'])
        by_source = {p['source']: p for p in a['reports']}
        assert len(by_source) == a['report_count'] == len(a['reports'])
        total_cases = []
        module_reviews = []
        for m in r['modules']:
            got = []
            report_reviews = []
            for rep in m['reports']:
                ar = by_source[rep['path']]
                assert rep['sha256'] == ar['raw_sha256'] == sha(ar['source'])
                assert sha(ar['archive']) == ar['archive_sha256']
                rc = cases(ar['source'])
                ac = cases(ar['archive'])
                assert rc == ac
                mt = path(ar['source']).stat().st_mtime
                assert abs(mt - stamp(ar['source_mtime_utc'])) < 0.000002
                assert start <= mt <= end and ar['within_run_interval']
                assert len(rc) == rep['tests'] == ar['testcases'] == rep['passed'] == rep['executed']
                assert all(x['status'] == 'passed' for x in rc)
                got += rc
                report_reviews.append(ar)
            got = sorted(got, key=lambda x: (x['classname'], x['name'], x['status']))
            assert got == sorted(m['testcases'], key=lambda x: (x['classname'], x['name'], x['status']))
            assert len(got) == m['tests'] == m['passed'] == m['executed'] > 0
            assert not m['failures'] and not m['errors'] and not m['skipped'] and not m['unexpected_skipped']
            total_cases += got
            if m['module'] in ('calf-io', 'calf-file-picker'):
                task = m['task']
                markers = [{'line': i, 'text': s} for i, s in enumerate(lines, 1) if s == '> Task ' + task or s.startswith('> Task ' + task + ' ')]
                assert len(markers) == 1 and markers[0]['text'] == '> Task ' + task
                rt = [{'line': i, 'text': s} for i, s in enumerate(lines, 1) if s.startswith('NATIVECMPKIT_TEST_RUNTIME task=' + task + ' ')]
                assert len(rt) == 1
                pm = next(x for x in plan['expected'] if x['module'] == m['module'])
                source_hashes = {p: sha(p) for p in pm['test_source_files']}
                assert all(before[p] == h for p, h in source_hashes.items())
                declared = []
                for p in source_hashes:
                    source = path(p).read_text()
                    found = [quoted or identifier for quoted, identifier in re.findall(r'@Test\s+fun\s+(?:`([^`]+)`|(\w+))\s*\(', source)]
                    if found:
                        # These reviewed files have one test class named for the file;
                        # expect fixture declarations may appear before that class.
                        cls = path(p).stem.split('.')[0]
                        assert re.search(r'\bclass\s+' + re.escape(cls) + r'\b', source)
                        declared += [(cls, n, 'passed') for n in found]
                assert sorted(declared) == sorted(normcase(x) for x in got), (name, m['module'], 'source/case mismatch')
                module_reviews.append({'module': m['module'], 'task': task, 'markers': markers, 'runtime_markers': rt, 'passed_cases': len(got), 'reports': report_reviews, 'cases': got, 'selected_test_source_hashes': source_hashes, 'exact_declared_method_set_matches_xml': True})
        assert len(total_cases) == a['totals']['tests'] == a['totals']['executed'] == a['totals']['passed'] == r['totals']['passed']
        assert a['totals'] == r['totals']
        assert len(r['modules']) == a['modules_requested'] == a['modules_with_test_execution'] == len(plan['expected'])
        assert len(by_source) == sum(len(m['reports']) for m in r['modules'])
        coil = [{'line': i, 'text': s} for i, s in enumerate(lines, 1) if s.startswith('> Task :calf-file-picker-coil:')]
        io_compile = [{'line': i, 'text': s} for i, s in enumerate(lines, 1) if s.startswith('> Task :calf-io:') and any(v in s for v in ['compileKotlin', 'compileTest', 'ProcessResources', 'unpackSkiko'])]
        context_basic = None
        if (d / 'browser-context').is_dir():
            ctx = read(d / 'browser-context/context.json')
            for row in ctx['paths']:
                assert sha(row['path']) == row['sha256']
            assert len(ctx['paths']) == 5
            assert len(coil) == 4 and all('PackageJson UP-TO-DATE' in s['text'] for s in coil)
            context_basic = {'path': str((d / 'browser-context/context.json').relative_to(ROOT)), 'sha256': sha(d / 'browser-context/context.json'), 'selected_external_file_hashes_checked': 5, 'installed_browser': ctx['installed_browser'], 'ordinary_frozen_dependency_verified': ctx['ordinary_frozen_dependency_verified']}
        result = {'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'archive': str((d / 'archive.json').relative_to(ROOT)), 'archive_sha256': sha(d / 'archive.json'), 'manifest': mani, 'raw_metadata_pairs_checked': len(a['archives']), 'report_pairs_checked': len(by_source), 'identical_raw_archived_case_identities_and_statuses': len(total_cases), 'raw_report_mtimes_match_and_inside_interval': True, 'command': a['command'], 'execution': a['execution'], 'started_utc': a['started_utc'], 'finished_utc': a['finished_utc'], 'complete_suite_requested': a['complete_suite_requested'], 'passed': True, 'totals': a['totals'], 'modules_requested': a['modules_requested'], 'modules_executed': a['modules_with_test_execution'], 'selected_input_count': 693, 'selected_input_raw_json_sha256': sha(d / 'inputs-before.json'), 'selected_input_sorted_digest': digest(before), 'all_selected_inputs_equal_before_after_and_current': True, 'owned_input_count': len(owned), 'owned_input_map_canonical_sha256': canon(owned), 'modules': module_reviews, 'coil_task_markers': coil, 'io_compile_resource_markers': io_compile, 'runtime': runtime, 'runtime_sha256': sha(d / 'runtime.json'), 'browser_context': context_basic}
        cd = ROOT / 'docs/development/evidence' / (name + '-context')
        c = read(cd / 'context-review.json')
        launch = read(cd / 'launcher.json')
        finish = read(cd / 'result.json')
        assert sha(cd / 'context-review.json') == CTX[name] and c['archive'] == result['archive'] and c['archive_sha256'] == result['archive_sha256']
        cm = manifest(cd)
        assert launch['extra_inputs_before'] == finish['extra_inputs_after']
        for p, h in launch['extra_inputs_before'].items():
            assert sha(p) == h, p
        assert digest(before) == launch['selected_input_digest'] == finish['selected_input_digest_after']
        assert finish['helper_receipt_sha256'] == sha(d / 'receipt.json') == sha(finish['helper_receipt'])
        assert not finish['selected_changes'] and not finish['extra_input_changes'] and finish['exit_code'] == 0
        assert launch['source_revision'] == finish['source_revision_after'] == BASE
        assert c['execution'] == a['execution'] and c['library_gate_passed']
        config_reviews = []
        if 'config_observations' in c:
            assert c['launcher_context_sha256'] == sha(cd / 'launcher.json') and c['launcher_result_sha256'] == sha(cd / 'result.json')
            assert not c['config_review_errors'] and not c['extra_input_changes_at_collection'] and not c['extra_input_changes_during_run']
            assert c['command'] == a['command']
            assert {x['task'] for x in c['config_observations']} == {m['task'] for m in r['modules']}
            roots = set()
            for cfg in c['config_observations']:
                q = path(cfg['raw_config'])
                s = q.read_text()
                assert not q.is_symlink() and sha(q) == cfg['raw_sha256']
                prefix = re.match(r'\s*module\.exports\s*=\s*function\(config\)\s*\{\s*config\.set\(', s)
                assert prefix
                tail = s[prefix.end():].lstrip()
                literal, offset = json.JSONDecoder().raw_decode(tail)
                assert tail[offset:].lstrip().startswith(');')
                subset = {k: literal[k] for k in ('basePath', 'browsers', 'files', 'frameworks', 'preprocessors', 'customContextFile', 'customDebugFile') if k in literal}
                assert sha(cd / cfg['selected_first_literal_config']) == cfg['selected_sha256'] and read(cd / cfg['selected_first_literal_config']) == subset
                refs = [literal[k] for k in ('customContextFile', 'customDebugFile') if k in literal] + literal['files']
                assert all(isinstance(x, str) for x in refs)
                cr = sorted({x.split('/node_modules/', 1)[0] for x in refs if '/node_modules/' in x})
                roots.update(cr)
                assert cr == cfg['node_modules_roots']
                mt = q.stat().st_mtime
                assert abs(mt - stamp(cfg['mtime_utc'])) < 0.000002 and start <= mt <= end and cfg['within_run_interval']
                assert s.count('config.set(') == cfg['total_config_set_occurrences']
                config_reviews.append(cfg)
            assert sorted(roots) == c['observed_node_modules_roots'] and len(config_reviews) == 19
            prepared = [p for p in launch['extra_inputs_before'] if launch['expected_tooling_destination'] and p.startswith(launch['expected_tooling_destination'] + '/')]
            if r['suite'] == 'wasm':
                assert roots == {launch['expected_tooling_destination']} and c['requested_prepared_home_used_in_fresh_configs'] and len(prepared) == 5 and len(launch['extra_inputs_before']) == 12
            else:
                assert roots == {str(ROOT / 'build/js')} and not prepared and len(launch['extra_inputs_before']) == 7
        else:
            prepared = []
            assert c['launch_command'] == launch['command']
        ctx_result = {'path': str((cd / 'context-review.json').relative_to(ROOT)), 'sha256': sha(cd / 'context-review.json'), 'manifest': cm, 'launcher_sha256': sha(cd / 'launcher.json'), 'result_sha256': sha(cd / 'result.json'), 'launcher_command': launch['command'], 'extra_input_count': len(launch['extra_inputs_before']), 'extra_inputs_equal_before_after_and_current': True, 'extra_inputs': launch['extra_inputs_before'], 'raw_and_selected_config_pairs_checked': len(config_reviews), 'config_observations': config_reviews, 'prepared_tooling_file_count': len(prepared), 'requested_tooling_destination': launch.get('expected_tooling_destination'), 'observed_node_modules_roots': c.get('observed_node_modules_roots', []), 'first_literal_subset_only_no_js_execution': True if config_reviews else None}
        result['extra_context'] = ctx_result
        results[name] = result
    assert all(x == all_inputs[0] for x in all_inputs)
    wasm = {m['module']: sorted(normcase(x) for x in m['cases']) for m in results['wasm-full-004']['modules']}
    js = {m['module']: sorted(normcase(x) for x in m['cases']) for m in results['js-full-004']['modules']}
    assert wasm == js and sum(len(x) for x in wasm.values()) == 29
    return {'schema_version': 1, 'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_revision': BASE, 'dirty_source': True, 'runs': results, 'all_three_693_input_snapshots_identical': True, 'current_selected_inputs_all_equal': True, 'owned_browser_unique_source_methods': 29, 'owned_browser_executions': 58, 'paired_browser_owned_method_sets_equal': True, 'owned_input_hashes': {p: h for p, h in all_inputs[0].items() if p.startswith(OWNED)}}


if __name__ == '__main__':
    print(json.dumps(review_runs(), sort_keys=True))
