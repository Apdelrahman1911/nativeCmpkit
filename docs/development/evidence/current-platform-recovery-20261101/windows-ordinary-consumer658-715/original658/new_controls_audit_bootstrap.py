#!/usr/bin/env python3
"""Audit only the NEW passive control script; never execute proposal controllers."""
import json
import os
from pathlib import Path
import runpy
import sys

control, audit_path, *selections = sys.argv[1:]
control = Path(control).resolve()
audit_path = Path(audit_path).resolve()
project = Path('/root/projects/nativeCmpKit')
controller = control.with_name('javafx_ordinary_maven_consumer.py')
prohibited_modules = {'javafx_ordinary_maven_consumer', 'library_tests', 'webview_consumer', 'runtime_context',
                      'daemon_jvm', 'stage_private_web', 'private_web_resolution'}
attempts = []


def deny(event, reason):
    attempts.append({'event': event, 'contract': reason})
    raise RuntimeError('NEW source-control isolation refused: ' + reason)


def audit(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.forkpty',
                 'socket.connect', 'socket.connect_ex', 'socket.bind', 'socket.getaddrinfo', 'ctypes.dlopen'):
        deny(event, 'No process/native/network action inside passive source controls')
    if event == 'import':
        name = str(args[0]).split('.')[0]
        if name in prohibited_modules or name.startswith('test_'):
            deny(event, 'No target/helper/old-TestCase module imports')
    if event == 'exec':
        filename = getattr(args[0], 'co_filename', '')
        if filename == str(controller) or (filename and Path(filename).is_absolute() and Path(filename).is_relative_to(project)):
            deny(event, 'No ROOT or proposed controller code execution')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).absolute()
        mode = args[1]
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)) or (
            isinstance(mode, str) and any(letter in mode for letter in ('w', 'a', 'x', '+')))
        if writing and path != audit_path:
            deny(event, 'Only the new owned audit receipt may be written by the passive child')
    if event in ('os.remove', 'os.unlink', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.link', 'os.symlink'):
        deny(event, 'No source/ROOT/filesystem mutation inside passive controls')


sys.addaudithook(audit)
sys.argv = [str(control), *selections]
try:
    runpy.run_path(str(control), run_name='__main__')
finally:
    value = {'schema': 'nativecmpkit-new-route-source-control-isolation658-v1', 'passed': not attempts,
             'denied_attempts': attempts, 'target_controller_or_old_test_imports_permitted': False,
             'process_native_network_or_ROOT_writes_permitted': False,
             'scope': 'Audited NEW AST/text controls only; not native controller or OS sandbox attestation'}
    with audit_path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')
