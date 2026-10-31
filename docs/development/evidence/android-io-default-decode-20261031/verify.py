#!/usr/bin/env python3
"""Offline checksum/diff/AST reconstruction only; never run source models or builds."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def owned(relative):
    parts = PurePosixPath(relative)
    require(not parts.is_absolute() and all(p not in ('.', '..') for p in parts.parts),
            'Archive paths must be relative and confined')
    candidate = ROOT
    for part in parts.parts:
        candidate = candidate / part
        require(not candidate.is_symlink(), 'Archive symlinks are refused')
    require(candidate.is_file(), 'Required archive file is missing')
    return candidate


def load(relative):
    return json.loads(owned(relative).read_text(encoding='utf-8'))


def diffs(relative):
    lines = owned(relative).read_text(encoding='utf-8').splitlines(keepends=True)
    result, current, hunk = [], None, None
    for line in lines:
        if line.startswith('diff --git '):
            match = re.fullmatch(r'diff --git a/(\S+) b/(\S+)\n', line)
            require(match is not None and match[1] == match[2], 'Unexpected diff target')
            current = {'target': match[1], 'new': False, 'hunks': []}
            result.append(current)
            hunk = None
        elif line.startswith('@@ '):
            require(current is not None, 'Hunk without a diff target')
            match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', line)
            require(match is not None, 'Malformed diff hunk')
            hunk = {'old_start': int(match[1]), 'old_count': int(match[2] or '1'),
                    'new_start': int(match[3]), 'new_count': int(match[4] or '1'), 'body': []}
            current['hunks'].append(hunk)
        elif hunk is not None:
            require(line[:1] in (' ', '+', '-'), 'Unsupported diff body or newline marker')
            hunk['body'].append(line)
        elif line.startswith('new file mode '):
            require(current is not None and line == 'new file mode 100644\n', 'Unexpected new-file mode')
            current['new'] = True
        else:
            require(current is not None and line.startswith(('--- ', '+++ ', 'index ')),
                    'Unexpected diff metadata')
    require(result and len({item['target'] for item in result}) == len(result),
            'Missing or duplicate diff targets')
    for item in result:
        require(item['hunks'], 'Diff target without hunks')
        for h in item['hunks']:
            require(sum(s[:1] in (' ', '-') for s in h['body']) == h['old_count'], 'Old hunk count mismatch')
            require(sum(s[:1] in (' ', '+') for s in h['body']) == h['new_count'], 'New hunk count mismatch')
    return result


def transform(text, item, reverse=False):
    source = text.splitlines(keepends=True)
    output, cursor = [], 0
    for h in item['hunks']:
        first, second = (('new', 'old') if reverse else ('old', 'new'))
        start = h[first + '_start']
        count = h[first + '_count']
        pos = start - 1 if start else 0
        source_prefixes = (' ', '+') if reverse else (' ', '-')
        output_prefixes = (' ', '-') if reverse else (' ', '+')
        expected = [s[1:] for s in h['body'] if s[:1] in source_prefixes]
        replacement = [s[1:] for s in h['body'] if s[:1] in output_prefixes]
        require(len(expected) == count and len(replacement) == h[second + '_count'], 'Transform count mismatch')
        require(cursor <= pos <= len(source) and source[pos:pos + count] == expected,
                'Diff source preimage mismatch')
        output.extend(source[cursor:pos])
        output.extend(replacement)
        cursor = pos + count
    output.extend(source[cursor:])
    return ''.join(output)


def guard_class(tree, name):
    selected = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name]
    require(len(selected) == 1, 'Expected exactly one owning source-guard class')
    return selected[0]


def methods(cls):
    return [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]


def verify():
    raw_manifest = owned('manifest.json').read_bytes()
    manifest_hash = sha(raw_manifest)
    require(owned('manifest.sha256').read_text(encoding='utf-8') == manifest_hash + '  manifest.json\n',
            'Manifest anchor mismatch')
    manifest = json.loads(raw_manifest)
    files = manifest['payload_files']
    paths = [x['path'] for x in files]
    require(len(paths) == len(set(paths)), 'Duplicate checksum paths')
    allowed = set(paths) | set(manifest['exclusions_from_payload_checksums'])
    present = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() or p.is_symlink()}
    require(present <= allowed, 'Unmanifested archive payload')
    for entry in files:
        data = owned(entry['path']).read_bytes()
        require(len(data) == entry['bytes'] and sha(data) == entry['sha256'], 'Payload checksum mismatch')

    reconstructed = {}
    for entry in manifest['reconstructed_sources']:
        items = diffs(entry['new_file_patch'])
        require(len(items) == 1 and items[0]['target'] == entry['path'] and items[0]['new'],
                'Unexpected reconstructed new-file target')
        item = items[0]
        require(len(item['hunks']) == 1 and item['hunks'][0]['old_start'] == 0,
                'New-file diff must have one empty old preimage')
        text = transform('', item)
        data = text.encode('utf-8')
        require(len(data) == entry['bytes'] and sha(data) == entry['sha256'] and
                len(text.splitlines()) == entry['lines'], 'Reconstructed source checksum/line mismatch')
        reconstructed[entry['path']] = text

    delta = diffs(manifest['owning_delta'])
    require({x['target'] for x in delta} == set(reconstructed), 'Owning delta target mismatch')
    original = {}
    for item in delta:
        target = item['target']
        source = transform(reconstructed[target], item, reverse=True)
        expected = next(x['original_source_sha256'] for x in manifest['reconstructed_sources'] if x['path'] == target)
        require(sha(source.encode('utf-8')) == expected, 'Original red source reconstruction mismatch')
        require(transform(source, item) == reconstructed[target], 'Owning forward reconstruction mismatch')
        original[target] = source

    native_path = next(x for x in reconstructed if x.endswith('.kt'))
    guard_path = next(x for x in reconstructed if x.endswith('.py'))
    native = reconstructed[native_path]
    native_methods = re.findall(r'@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)', native)
    require(native_methods == manifest['junit_methods'], 'Native method identity/order mismatch')
    require(len(native.splitlines()) == len(original[native_path].splitlines()) == 370,
            'Native line count changed')
    require(Counter(x.strip() for x in native.splitlines() if x.strip()) ==
            Counter(x.strip() for x in original[native_path].splitlines() if x.strip()),
            'Native stripped-line multiset changed')

    original_ast = ast.parse(original[guard_path])
    repaired_ast = ast.parse(reconstructed[guard_path])
    old_class = guard_class(original_ast, 'AndroidIoDefaultDecodeGuards')
    repaired_class = guard_class(repaired_ast, 'AndroidIoDefaultDecodeGuards')
    old_methods = methods(old_class)
    new_methods = methods(repaired_class)
    require(len(old_methods) == 18 and len(new_methods) == 19, 'Guard declaration count mismatch')
    require({m.name for m in old_methods} == set(manifest['prior_modeled_methods']),
            'Prior guard identities mismatch')
    additions = [m for m in new_methods if m.name == manifest['new_owning_guard_method']]
    require(len(additions) == 1, 'Expected exactly one new owning guard')
    driver_ast = ast.parse(owned(manifest['standalone_source_guard']).read_text(encoding='utf-8'))
    driver_class = guard_class(driver_ast, 'BitmapOwnershipSourceRegression')
    driver_methods = methods(driver_class)
    require(len(driver_methods) == 1 and ast.dump(additions[0]) == ast.dump(driver_methods[0]),
            'Owning driver/source guard AST mismatch')
    repaired_class.body.remove(additions[0])
    require(ast.dump(original_ast) == ast.dump(repaired_ast), 'Prior guard/import/setup/helper AST changed')

    adapter = diffs('patches/finite-adapter.patch')
    require({item['target'] for item in adapter} == set(manifest['finite_adapter_targets']),
            'Finite adapter target mismatch')
    return {
        'schema_version': 1,
        'kind': 'Offline checksum/source-diff/Python-AST reconstruction, not model/build/native execution',
        'result': 'PASS',
        'manifest_sha256': manifest_hash,
        'payload_files_verified': len(files),
        'payload_bytes_verified': sum(x['bytes'] for x in files),
        'reconstructed_sources': [
            {'path': entry['path'], 'bytes': entry['bytes'], 'sha256': entry['sha256'], 'lines': entry['lines'],
             'reconstructed_original_source_sha256': entry['original_source_sha256']}
            for entry in manifest['reconstructed_sources']
        ],
        'owning_delta_reverse_and_forward_verified': True,
        'native_370_lines_stripped_line_multiset_and_three_junit_identities_retained': True,
        'prior_eighteen_guard_import_setup_helper_ast_identical': True,
        'one_new_guard_ast_matches_saved_red_green_driver': True,
        'finite_adapter_diff_targets_and_hunk_counts_verified': len(adapter),
        'current_repo_preimages_checked_or_adapter_applied': False,
        'python_models_executed': 0,
        'Kotlin_compiler_APK_emulator_native_CI_network_or_publishing_executions': 0,
        'fresh_nineteen_guard_suite_pass_claimed': False,
        'issue_closure_security_or_release_readiness_inferred': False,
    }


if __name__ == '__main__':
    try:
        result = verify()
    except (ValueError, KeyError, OSError, SyntaxError, StopIteration):
        print(json.dumps({'result': 'FAIL', 'scope': 'Offline source/archive integrity only'}, indent=2))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
