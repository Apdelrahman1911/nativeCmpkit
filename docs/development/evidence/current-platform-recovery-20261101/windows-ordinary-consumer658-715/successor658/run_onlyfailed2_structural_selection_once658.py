#!/usr/bin/env python3
"""Execute only the qualified failed owning graph1+failed NEW raw-capture1 once."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

PACKET = Path(__file__).resolve().parent
PLAN = PACKET / 'ONLYFAILED2-STRUCTURAL-EXECUTION-PLAN658.json'
QUALIFIED = PACKET / 'QUALIFIED-ONLYFAILED2-STRUCTURAL-SOURCE-INPUTS658.json'


def read(path, limit=64 * 1024**2):
    before = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or path.is_symlink() or before.st_nlink != 1 or before.st_size > limit:
        raise ValueError('Bounded regular execution input required')
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Execution input changed during read')
    return raw


def snapshot(files, absences, aliases):
    result = {}
    for name in sorted(files):
        raw = read(Path(name))
        result[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    absent = {name: not (Path(name).exists() or Path(name).is_symlink()) for name in sorted(absences)}
    observed_aliases = {name: str(Path(name).resolve(strict=True)) for name in sorted(aliases)}
    return {'files': result, 'ROOT_destinations_absent': absent, 'tool_aliases': observed_aliases}


def write(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')
    path.chmod(0o600)


if len(sys.argv) != 2 or sys.argv[1] != 'new-controls':
    raise SystemExit('One exact qualified execution stage required')
stage = sys.argv[1]
plan_raw = read(PLAN)
plan = json.loads(plan_raw)
qualified_raw = read(QUALIFIED)
qualified = json.loads(qualified_raw)
if qualified['passed'] is not True or qualified['plan_sha256'] != hashlib.sha256(plan_raw).hexdigest():
    raise SystemExit('Exact qualified execution plan required')
result_dir = PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658'
result_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
before = snapshot(qualified['inputs'], qualified['ROOT_destinations_absent'], qualified['tool_aliases'])
write(result_dir / 'source-inputs-before.json', before)
if before['files'] != {name: {key: row[key] for key in ('bytes', 'sha256')} for name, row in qualified['inputs'].items()} or not all(before['ROOT_destinations_absent'].values()) or before['tool_aliases'] != qualified['tool_aliases']:
    write(result_dir / 'pre-spawn-refusal.json', {'passed': False, 'command_started': False, 'contract': 'Source-qualified inputs or named ROOT absences changed; no command/retry'})
    raise SystemExit('Source qualification drift; child not started')
command = plan[stage]['command']
environment = {'PATH': '/usr/bin:/bin', 'TZ': 'UTC', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0'}
started_utc, began = datetime.now(timezone.utc).isoformat(), time.monotonic()
record = {'schema': 'nativecmpkit-javafx-onlyfailed2-structural-source-execution658-v1', 'stage': stage, 'command': command,
          'cwd': str(PACKET), 'started_utc': started_utc, 'plan_sha256': hashlib.sha256(plan_raw).hexdigest(),
          'qualification_map_sha256': hashlib.sha256(qualified_raw).hexdigest(), 'timeout_seconds': plan[stage]['timeout_seconds'],
          'target_imports_requested': 0, 'unchanged_method_populations_requested': 0, 'build_stage_native_dispatch_or_Git_commands_requested': 0,
          'automatic_retry': False, 'accepted_private_library_Stop_replayed': False,
          'failed_owning_existing_graph_methods_requested': 1, 'failed_original_NEW_raw_capture_methods_requested': 1,
          'accepted_NEW_coupling_method_replayed': False, 'unchanged_nine_replayed': False,
          'Actionlint_replayed': False, 'original_packet_changed': False}
try:
    with (result_dir / 'stdout.txt').open('xb') as stdout, (result_dir / 'stderr.txt').open('xb') as stderr:
        result = subprocess.run(command, cwd=PACKET, env=environment, stdout=stdout, stderr=stderr,
                                timeout=plan[stage]['timeout_seconds'], check=False)
    record['exit_code'] = result.returncode
except subprocess.TimeoutExpired:
    record['exit_code'] = None
    record['error'] = 'Passive tool deadline reached; preserve original streams and no retry'
finally:
    record['elapsed_seconds'] = round(time.monotonic() - began, 6)
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    after = snapshot(qualified['inputs'], qualified['ROOT_destinations_absent'], qualified['tool_aliases'])
    write(result_dir / 'source-inputs-after.json', after)
    record['source_inputs_held'] = before == after
    record['actual_named_input_count'] = len(before['files'])
    record['ROOT_absence_count'] = len(before['ROOT_destinations_absent'])
    record['streams'] = {}
    for name in ('stdout.txt', 'stderr.txt'):
        path = result_dir / name
        if path.exists():
            raw = read(path)
            record['streams'][name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    if stage == 'new-controls':
        audit_path = result_dir / 'audit.json'
        audit = json.loads(read(audit_path)) if audit_path.exists() else {'passed': False, 'contract': 'No child isolation finalizer receipt'}
        record['audit'] = audit
        record['selected_methods'] = plan[stage]['selected_methods']
        record['selected_method_count'] = len(plan[stage]['selected_methods'])
    else:
        record['optional_shellcheck_and_pyflakes'] = 'Disabled; only this Actionlint YAML/expression/action source validation is requested'
        record['workflow_source_only'] = True
    record['passed'] = record.get('exit_code') == 0 and record['source_inputs_held'] and (stage != 'new-controls' or record['audit']['passed'])
    record['scope'] = 'Only failed owning graph1 plus failed original NEW raw-capture1 structural AST/text controls' if stage == 'new-controls' else 'Candidate existing-workflow Actionlint source validation only; no native/dispatch/old method execution'
    write(result_dir / 'result.json', record)
print(json.dumps(record, sort_keys=True))
raise SystemExit(0 if record['passed'] else 1)
