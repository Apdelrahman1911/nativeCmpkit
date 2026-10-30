#!/usr/bin/env python3
"""Exact configured dependency-input cache key, not compiled/test-result reuse.

Never includes a commit SHA, library sources, documentation/metadata archives,
candidate binaries, project outputs or tests XML in the key or cached paths.
Configured Gradle/convention/Cargo/Yarn inputs and controller/toolchain recipes
bind the cache conservatively. Dependencies remain untrusted; a matching cache
does not attest checksum provenance, runtime results or release readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import library_tests as lt

ROOT = Path(__file__).resolve().parents[2]
SCOPES = ('libraries', 'core-io', 'webview')
MAX_FILES = 4096
MAX_INPUT_BYTES = 8 * 1024**2
RECIPE_FILES = ('scripts/ci/dependency_cache_inputs.py', 'scripts/ci/library_tests.py',
                'scripts/ci/runtime_context.py')
PROJECT_FILES = ('build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'gradle.lockfile',
                 'package.json', 'yarn.lock', 'package-lock.json', 'pnpm-lock.yaml')


def selection_contract(root: Path, selected_csv: str) -> dict:
    """Canonical module-set identity, never a raw CSV/path in an Actions key.

    Cache keys cannot contain commas. Do not merely remove punctuation: that
    would risk merging different module sets. Validate the exact configured
    paths, reject duplicates/empty/unknown elements, then hash a sorted,
    versioned JSON identity. This partitions dependencies, not test results.
    """
    if type(selected_csv) is not str or len(selected_csv) > 4096:
        raise ValueError('Expected a bounded exact module selector')
    if selected_csv == '':
        return {'cache_key': 'all', 'modules': []}
    modules = selected_csv.split(',')
    projects = lt.projects(root)
    if len(modules) != len(set(modules)) or len(modules) > len(projects) or any(
            not re.fullmatch(r'[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)*', name) or name not in projects
            for name in modules):
        raise ValueError('Expected unique canonical configured module paths')
    modules.sort()
    payload = json.dumps({'schema': 'nativecmpkit-cache-selection-v1', 'modules': modules},
                         separators=(',', ':'), sort_keys=True).encode()
    return {'cache_key': 'subset-' + hashlib.sha256(payload).hexdigest(), 'modules': modules}


def selected_inputs(root: Path, scope: str) -> dict[str, str]:
    if scope not in SCOPES:
        raise ValueError('Unknown fixed dependency-cache scope')
    projects = lt.projects(root)
    settings = lt.safe_path(root, 'settings.gradle.kts').read_text(encoding='utf-8')
    block = re.findall(r'(?ms)^include\(\s*(.*?)^\)', settings)[0]
    samples = {name.removeprefix(':').replace(':', '/') for name in re.findall(r'"(:sample:[a-z][a-z0-9-]*)"',
                re.sub(r'(?m)//[^\n]*', '', block))}
    paths = set()

    def optional(relative):
        path = lt.safe_path(root, relative)
        if path.exists():
            if not path.is_file():
                raise ValueError('Expected a regular dependency-config input')
            paths.add(path)

    def tree(relative):
        paths.update(lt.source_files(root, relative))

    for relative in (*lt.ROOT_INPUTS, *RECIPE_FILES, 'convention-plugins/build.gradle.kts',
                     'convention-plugins/settings.gradle.kts'):
        optional(relative)
    for relative in ('gradle', 'convention-plugins/src', 'convention-plugins/gradle',
                     'convention-plugins/.cargo', '.cargo', 'kotlin-js-store'):
        tree(relative)
    for project in sorted(set(projects) | samples):
        if not lt.safe_path(root, project + '/build.gradle.kts').is_file():
            raise ValueError('Missing configured project dependency input')
        for name in PROJECT_FILES:
            optional(project + '/' + name)
        for name in ('gradle', '.cargo', 'native/.cargo'):
            tree(project + '/' + name)
        for name in ('Cargo.toml', 'Cargo.lock', 'build.rs', 'rust-toolchain.toml'):
            optional(project + '/native/' + name)
    if scope == 'libraries':
        for fixture in ('tests/consumer/android-geo-probe', 'tests/consumer/android-share-recipient',
                        'tests/consumer/android-share-documents', 'tests/consumer/android-camera-receiver'):
            for name in PROJECT_FILES:
                optional(fixture + '/' + name)
    if scope == 'core-io':
        for fixture in ('tests/consumer', 'tests/consumer/io-desktop'):
            for name in PROJECT_FILES:
                optional(fixture + '/' + name)
            tree(fixture + '/gradle')
        for name in ('scripts/ci/core_io_consumer.py', 'scripts/ci/stage-core-io.init.gradle.kts',
                     'tests/consumer/verify_artifacts.py', 'docs/migration/identity.json'):
            optional(name)
    if scope == 'webview':
        for name in PROJECT_FILES:
            optional('tests/consumer/webview-desktop/' + name)
        for name in ('scripts/ci/webview_consumer.py', 'scripts/ci/stage-webview.init.gradle.kts',
                     'scripts/ci/webview-consumer-daemon.init.gradle.kts', 'tests/consumer/verify_artifacts.py',
                     'docs/migration/identity.json'):
            optional(name)
    if not paths or len(paths) > MAX_FILES:
        raise ValueError('Missing or unbounded selected dependency inputs')
    result = {}
    for path in sorted(paths):
        before = path.stat()
        if before.st_nlink != 1 or before.st_size > MAX_INPUT_BYTES:
            raise ValueError('Dependency input must be bounded and unshared')
        result[path.relative_to(root).as_posix()] = lt.sha256(path)
        after = path.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('Dependency input changed while hashing')
    return dict(sorted(result.items()))


def fingerprint(scope: str, inputs: dict[str, str]) -> str:
    # Content keys deliberately exclude the observed revision and machine paths.
    return lt.input_digest({'dependency-cache-scope-' + scope: 'nativecmpkit-deps-v2', **inputs})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=SCOPES, required=True)
    parser.add_argument('--selection', default='', help='Exact comma-separated configured library module paths')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.scope != 'libraries' and args.selection:
        raise ValueError('Only the library scope accepts a module subset')
    selection = selection_contract(ROOT, args.selection)
    output = lt.safe_path(ROOT, args.output)
    base = lt.safe_path(ROOT, 'build/ci-runtime')
    if output == base or not output.is_relative_to(base) or output.suffix != '.json' or output.exists():
        raise ValueError('Use a fresh confined CI runtime JSON receipt')
    selected = selected_inputs(ROOT, args.scope)
    result = {'schema_version': 1, 'scope': args.scope, 'source_revision': lt.git_revision(ROOT),
              'observed_utc': lt.utc_now(), 'dependency_input_count': len(selected),
              'dependency_inputs_sha256': fingerprint(args.scope, selected), 'inputs': selected,
              'selection_cache_key': selection['cache_key'], 'selected_modules': selection['modules'],
              'compiled_or_test_results_reused': False, 'ordinary_dependency_trust_certified': False,
              'release_readiness_certified': False}
    if selected_inputs(ROOT, args.scope) != selected:
        raise ValueError('Selected dependency inputs changed during observation')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(result['dependency_inputs_sha256'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
