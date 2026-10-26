#!/usr/bin/env python3
"""Read-only v2 proposal/evidence readback; no Gradle/Groovy/Node/Yarn execution.

Only --report tooling-scope-verificationNNN.json creates an exclusive receipt.
Checks hashes, class bytes and local documentation links, not runtime behavior.
The live evidence index is checked separately after the new receipt exists.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[4]
CORE_API = Path('/root/.gradle/wrapper/dists/gradle-9.7.1-bin/1w1c7tv4s851m17nbqdsro2tv/gradle-9.7.1/lib/gradle-core-api-9.7.1.jar')
V2 = 'scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md'
V2_SHA = 'e1697dc6345bc9e5fb4f2b78a2f3ea86f796929184e272fdfc634afbc32d338d'
checks = 0
inputs = {}


def check(ok, message):
    global checks
    checks += 1
    if not ok:
        raise ValueError(message)


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    check('..' not in path.parts and (path.is_relative_to(REPO) or path == CORE_API), 'Unexpected input scope')
    check(path.is_file() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents), 'Missing/symlink input')
    data = path.read_bytes()
    name = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    digest = hashlib.sha256(data).hexdigest()
    check(name not in inputs or inputs[name] == digest, 'Input changed during readback: ' + name)
    inputs[name] = digest
    return data


def bound(path, digest):
    check(hashlib.sha256(read(path)).hexdigest() == digest, 'Hash mismatch: ' + str(path))


def verify():
    checkpoint = json.loads(read(BASE / 'wasm-tooling-init-scope-checkpoint001.json'))
    for row in checkpoint['original_records']:
        bound(row['path'], row['sha256'])
    index = checkpoint['original_index']
    bound(index['snapshot_path'], index['sha256'])
    old = json.loads(read(BASE / 'documentation-verification001.json'))
    check(old['inspected_file_sha256'][index['path']] == index['sha256'], 'Original index is not preserved')
    scope = json.loads(read(BASE / 'wasm-tooling-init-scope-review002.json'))
    for path, meta in scope['input_hashes'].items():
        bound(path, meta['sha256'])
    bound(V2, V2_SHA)
    check(scope['proposal']['path'] == V2 and scope['proposal']['sha256'] == V2_SHA, 'Wrong v2 binding')
    for flag in ('groovy_compilation_attempted', 'gradle_invocation_attempted',
                 'actual_settings_callbacks_observed', 'actual_task_graph_captured',
                 'actual_yarn_process_captured', 'node_yarn_or_network_invocation_attempted',
                 'root_or_convention_edited', 'parser_implemented', 'policy_adopted'):
        check(scope[flag] is False, 'Unexecuted scope changed: ' + flag)
    check(scope['library_tests_executed'] == 0, 'Data checks must not be tests')
    check(scope['inspection_command']['exit_code'] == 0 and scope['inspection_command']['stderr_bytes'] == 0, 'API lookup failed')
    check(len(scope['classes']) == 4 and scope['public_signature_count'] == 11, 'API scope changed')
    for row in scope['classes']:
        check(row['artifact'] == str(CORE_API), 'Unexpected class artifact')
        with zipfile.ZipFile(CORE_API) as jar:
            check(hashlib.sha256(jar.read(row['jar_entry'])).hexdigest() == row['class_sha256'], 'Class bytes changed')
    reviewer_path = 'docs/development/evidence/review/dependency-tooling-independent.json'
    reviewer = json.loads(read(reviewer_path))['wasm_tooling_init_scope_review']
    corrected = reviewer['corrected_proposal']
    check(corrected['path'] == V2 and corrected['sha256'] == V2_SHA, 'Reviewer approved different bytes')
    check(corrected['scope_decision'].startswith('GREEN for source-only'), 'No source-only scope acceptance')
    for flag in ('reviewer_gradle_java_javap_jcmd_node_yarn_or_network_executed',
                 'reviewer_proposal_or_source_edited', 'production_dependencies_verified',
                 'independent_trust_reviewed', 'build007_closed'):
        check(reviewer[flag] is False, 'Independent review scope changed')
    read('docs/development/evidence/review/dependency-tooling-independent.md')
    links = []
    for path in (REPO / V2, BASE / 'wasm-tooling-init-scope-review002.md', REPO / index['snapshot_path']):
        source = read(path).decode()
        refs = dict(re.findall(r'^\[([^\]]+)\]:\s+(\S+)\s*$', source, re.MULTILINE))
        for name in re.findall(r'\[[^\]]*\]\[([^\]]+)\]', source):
            check(name in refs, 'Undefined Markdown reference')
        targets = list(refs.values()) + re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)', source)
        for link in targets:
            parsed = urlsplit(link)
            check(not parsed.scheme and not parsed.netloc, 'External links are not checked')
            target = (path.parent / unquote(parsed.path)).resolve()
            check(target.is_relative_to(REPO) and target.exists(), 'Missing/out-of-repository link: ' + link)
            links.append({'document': str(path.relative_to(REPO)), 'target': str(target.relative_to(REPO))})
    check(not (REPO / 'scripts/dependencies/yarn/__init__.py').exists(), 'Sibling unittest discovery boundary changed')
    for path, digest in list(inputs.items()):
        bound(path, digest)
    return {'class_hash_checks': 4, 'public_signatures_in_recorded_javap': 11,
            'local_links': links, 'independent_scope_decision': corrected['scope_decision'],
            'live_index_link_check': 'Separate existing documentation verifier after this receipt exists'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.report:
        check(re.fullmatch(r'tooling-scope-verification[0-9]{3}\.json', args.report), 'Invalid report name')
        check(not (BASE / args.report).exists() and not (BASE / args.report).is_symlink(), 'Existing receipt')
    record = {'argv': sys.argv, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'proposal/source/API/documentation readback, not executable integration',
              'gradle_groovy_node_yarn_or_network_executed': False, 'library_tests_executed': 0,
              'policy_or_release_gate_passed': False, 'error': None}
    try:
        record.update(verify())
    except Exception as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
    record.update(exit_code=1 if record['error'] else 0, checks=checks,
                  inspected_file_sha256=inputs, ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if args.report:
        with (BASE / args.report).open('x') as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps({key: record.get(key) for key in ('exit_code', 'error', 'checks', 'class_hash_checks')}, indent=2))
    return record['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
