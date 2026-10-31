#!/usr/bin/env python3
"""One source-bound macOS SDK help/identity observation; no app or library work."""
from __future__ import annotations
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = 'build/ci-verification/apple-appinfo-capability'
SOURCE_INPUTS = ('.github/workflows/gradle.yml', 'scripts/ci/workflow_matrix.py',
                 'scripts/ci/apple_appinfo_capability.py', 'scripts/ci/test_apple_appinfo_capability.py')
MAX_COMMAND_BYTES, MAX_TOTAL_BYTES, MAX_TOOL_BYTES = 128*1024, 512*1024, 128*1024**2
COMMAND_SECONDS, TOTAL_SECONDS = 15, 90
COMMANDS = {
    'source': ('/usr/bin/git', 'rev-parse', 'HEAD'),
    'clean': ('/usr/bin/git', 'status', '--porcelain', '--untracked-files=normal'),
    'developer': ('/usr/bin/xcode-select', '--print-path'),
    'simctl': ('/usr/bin/xcrun', '--find', 'simctl'),
    'xcodebuild': ('/usr/bin/xcrun', '--find', 'xcodebuild'),
    'xcode-version': ('/usr/bin/xcrun', 'xcodebuild', '-version'),
    'help': ('/usr/bin/xcrun', 'simctl', 'help', 'appinfo'),
}


class CapabilityError(ValueError):
    """Fixed source guards only; never include raw output, paths or exception bodies."""


@dataclass(frozen=True)
class Result:
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    stop_reason: str | None


def need(value, guard):
    if not value: raise CapabilityError(guard)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def host():
    return {'system':platform.system(), 'architecture':platform.machine().lower(),
            'python':platform.python_version()}


def stop(process):
    """Signal only an anchored owned session; never signal after an owned wait."""
    pid=process.pid
    need(type(pid) is int and pid>1 and pid not in (os.getpgrp(),os.getsid(0)),
         'owned_control_process_group_required')
    if process.returncode is not None:
        # Once reaped, a group identifier may be reused. Never signal it again.
        try: os.killpg(pid,0)
        except ProcessLookupError: return
        raise CapabilityError('reaped_control_group_still_present')
    def completed_or_refuse(guard):
        # ESRCH is not proof of completion. Wait only this Popen-owned child,
        # then accept only a missing group. A live/reused group is never signalled.
        try: code=process.wait(timeout=2)
        except subprocess.TimeoutExpired: raise CapabilityError(guard) from None
        need(type(code) is int and type(process.returncode) is int and
             process.returncode==code,'owned_control_exit_unobserved')
        try: os.killpg(pid,0)
        except ProcessLookupError: return True
        raise CapabilityError('reaped_control_group_still_present')
    def anchored_signal(value):
        # Cached returncode, not poll(): the unreaped child anchors PID/SID.
        try:
            group,session=os.getpgid(pid),os.getsid(pid)
        except ProcessLookupError:
            return completed_or_refuse('owned_control_leader_unavailable')
        need(group==pid and session==pid,'owned_control_session_changed')
        try: os.killpg(pid,value)
        except ProcessLookupError:
            return completed_or_refuse('owned_control_group_unavailable')
        return False
    if anchored_signal(signal.SIGTERM): return
    time.sleep(.05)
    if anchored_signal(signal.SIGKILL): return
    process.wait(timeout=2)


def capture(argv, cwd, timeout):
    """Bound pipe reads; preserve partial metadata if the single owned stop refuses."""
    outputs = {'stdout':bytearray(), 'stderr':bytearray()}
    deadline, reason, stop_attempted = time.monotonic()+timeout, None, False
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    def owned_stop():
        nonlocal stop_attempted
        stop_attempted=True
        stop(process)
    try:
        try:
            with selectors.DefaultSelector() as selected:
                for name in outputs: selected.register(getattr(process,name), selectors.EVENT_READ, name)
                while selected.get_map() and reason is None:
                    if time.monotonic() >= deadline:
                        reason='timeout'; break
                    for key,_ in selected.select(min(.05,max(0,deadline-time.monotonic()))):
                        chunk=os.read(key.fileobj.fileno(),4096)
                        if not chunk:
                            selected.unregister(key.fileobj); continue
                        available=MAX_COMMAND_BYTES-sum(len(body) for body in outputs.values())
                        outputs[key.data].extend(chunk[:available])
                        if len(chunk)>available:
                            reason='output-bound'; break
                if reason is not None:
                    owned_stop()
                else:
                    try: process.wait(timeout=max(.001,deadline-time.monotonic()))
                    except subprocess.TimeoutExpired:
                        reason='timeout';owned_stop()
        finally:
            if not stop_attempted: owned_stop()
    except CapabilityError as error:
        # No success inference: an unknown exit remains None, with a fixed stop
        # reason. collect records only bounded hashes before re-raising this guard.
        error.control_result=Result(process.returncode,bytes(outputs['stdout']),
                                    bytes(outputs['stderr']),reason or 'owned-control-refusal')
        raise
    finally:
        process.stdout.close();process.stderr.close()
    return Result(process.returncode,bytes(outputs['stdout']),bytes(outputs['stderr']),reason)


def control(argv, cwd, timeout):
    need(tuple(argv) in COMMANDS.values(), 'nonfixed_control_command')
    return capture(tuple(argv),cwd,timeout)


def valid(result):
    return (isinstance(result,Result) and type(result.exit_code) is int and
            isinstance(result.stdout,bytes) and isinstance(result.stderr,bytes) and
            len(result.stdout)+len(result.stderr)<=MAX_COMMAND_BYTES and result.stop_reason is None)


def metadata(result):
    return {'exit_code':result.exit_code, 'stop_reason':result.stop_reason,
            'stdout_bytes':len(result.stdout), 'stdout_sha256':digest(result.stdout),
            'stderr_bytes':len(result.stderr), 'stderr_sha256':digest(result.stderr)}


def help_observation(result):
    value = {'status':'unavailable','capability_available':False,'known_syntax':None,
             'appinfo_output_schema_observed':False,'native_functionality_verified':False,
             'raw_help_or_paths_uploaded':False}
    if not valid(result): return value
    value.update(metadata(result))
    if result.exit_code != 0: return value
    try: text=(result.stdout+b'\n'+result.stderr).decode('utf-8',errors='strict')
    except UnicodeError: return value
    # One exact source-reviewed usage form, not a substring/catchall parser.
    syntax='simctl appinfo <device> <app bundle identifier>'
    usages=re.findall(r'(?m)^Usage:[ \t]*([^\r\n]+)\r?$',text)
    if usages == [syntax]:
        value.update(status='observed-supported-syntax',capability_available=True,known_syntax=syntax)
    return value


def file_digest(path):
    before=path.stat()
    need(path.is_file() and not path.is_symlink() and 0<before.st_size<=MAX_TOOL_BYTES,'expected_regular_bounded_file')
    value=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''): value.update(chunk)
    after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'file_changed_during_identity_read')
    return before.st_size,value.hexdigest()


def tool_identity(path, basename):
    need(path.is_absolute() and path.name==basename,'exact_selected_tool_path_required')
    size,value=file_digest(path)
    return {'basename':basename,'bytes':size,'sha256':value,'path_sha256':digest(str(path).encode()),
            'canonical_path_sha256':digest(str(path.resolve(strict=True)).encode())}


def actual_path(result):
    need(valid(result) and result.exit_code==0,'path_control_unavailable')
    try: text=result.stdout.decode('utf-8',errors='strict').strip()
    except UnicodeError: raise CapabilityError('path_control_encoding') from None
    need(0<len(text)<=4096 and not any(c in text for c in '\r\n\0') and Path(text).is_absolute(),
         'bounded_absolute_selected_path_required')
    return Path(text)


def fresh_output(root):
    current=root
    for component in Path(OUTPUT).parts:
        current=current/component
        need(not current.is_symlink(),'output_parent_symlink')
        if component==Path(OUTPUT).name:
            need(not current.exists(),'output_already_exists')
            current.mkdir(mode=0o700)
        else:
            current.mkdir(exist_ok=True)
            need(current.is_dir(),'output_parent_not_directory')
    return current


def collect(root=ROOT, *, control=control):
    output=fresh_output(root)
    private=output/'private';private.mkdir(mode=0o700)
    started=time.monotonic();owned=[];total=0
    receipt={'schema_version':1,'operation':'appinfo-help-capability','status':'unavailable',
             'capability_available':False,'subsequent_appinfo_ready':False,
             'appinfo_output_schema_observed':False,'native_functionality_verified':False,
             'packages_published':False,'release_readiness_certified':False,
             'raw_help_or_paths_uploaded':False,'commands':[],
             'started_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    def call(name):
        nonlocal total
        remaining=TOTAL_SECONDS-(time.monotonic()-started)
        need(remaining>0,'total_discovery_timeout')
        timeout=min(COMMAND_SECONDS,remaining)
        control_error=None
        try: result=control(COMMANDS[name],root,timeout)
        except CapabilityError as error:
            result=getattr(error,'control_result',None)
            if result is None: raise
            control_error=error
        need(isinstance(result,Result) and
             (type(result.exit_code) is int or (control_error is not None and result.exit_code is None)) and
             isinstance(result.stdout,bytes) and isinstance(result.stderr,bytes),'control_result_shape')
        if control_error is not None:
            need(result.stop_reason in ('timeout','output-bound','owned-control-refusal'),
                 'partial_control_stop_reason_required')
        need(len(result.stdout)+len(result.stderr)<=MAX_COMMAND_BYTES,'control_output_bound')
        total+=len(result.stdout)+len(result.stderr)
        need(total<=MAX_TOTAL_BYTES,'total_private_output_bound')
        index=len(receipt['commands'])+1
        for suffix in ('stdout','stderr'):
            path=private/f'{index:02}-{name}.{suffix}';body=getattr(result,suffix)
            descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(descriptor,'wb') as target: target.write(body)
            info=path.stat();owned.append((path,info.st_dev,info.st_ino,len(body),digest(body)))
        entry={'name':name,'argv':list(COMMANDS[name]),'timeout_seconds':timeout,**metadata(result)}
        if control_error is not None:
            entry.update(control_error_guard=str(control_error),owned_control_cleanup_refused=True)
        receipt['commands'].append(entry)
        if control_error is not None: raise control_error
        need(result.stop_reason is None,'control_stopped_before_complete_output')
        return result
    try:
        receipt['host']=host()
        need(receipt['host']['system']=='Darwin' and receipt['host']['architecture']=='arm64','actual_Darwin_arm64_required')
        need(shutil.disk_usage(root)[2]>=8192*1024**2+MAX_TOTAL_BYTES,'eight_GiB_reserve_required')
        receipt['disk_reserve_verified']=True
        source=call('source')
        need(source.exit_code==0 and re.fullmatch(rb'[0-9a-f]{40}\n?',source.stdout),'exact_source_revision_required')
        receipt['source_revision']=source.stdout.decode().strip()
        clean=call('clean');need(clean.exit_code==0 and not clean.stdout.strip(),'clean_source_required')
        receipt['source_tree_dirty']=False
        receipt['inputs_before']={name:file_digest(root/name)[1] for name in SOURCE_INPUTS}
        developer=actual_path(call('developer'))
        need(developer.is_dir(),'selected_developer_directory_unavailable')
        receipt['developer_directory_sha256']=digest(str(developer).encode())
        receipt['developer_directory_canonical_sha256']=digest(str(developer.resolve(strict=True)).encode())
        simctl=actual_path(call('simctl'));xcodebuild=actual_path(call('xcodebuild'))
        receipt['tool_identities']={name:tool_identity(path,name) for name,path in
                                    (('xcrun',Path('/usr/bin/xcrun')),('simctl',simctl),('xcodebuild',xcodebuild))}
        version=call('xcode-version')
        need(valid(version) and version.exit_code==0,'xcode_version_control_unavailable')
        match=re.fullmatch(rb'Xcode ([0-9]+(?:\.[0-9]+){1,2})\r?\nBuild version ([A-Za-z0-9.]{1,64})\r?\n?',version.stdout)
        need(match is not None,'xcode_version_shape_unavailable')
        receipt['xcode']={'version':match[1].decode(),'build':match[2].decode()}
        receipt['help']=help_observation(call('help'))
        receipt['inputs_after']={name:file_digest(root/name)[1] for name in SOURCE_INPUTS}
        after=call('source');clean_after=call('clean')
        need(after.exit_code==0 and after.stdout.decode().strip()==receipt['source_revision'] and
             clean_after.exit_code==0 and not clean_after.stdout.strip() and
             receipt['inputs_before']==receipt['inputs_after'],'source_identity_changed')
        receipt['source_revision_after']=after.stdout.decode().strip()
        need(all(tool_identity(path,name)==receipt['tool_identities'][name] for name,path in
                 (('xcrun',Path('/usr/bin/xcrun')),('simctl',simctl),('xcodebuild',xcodebuild))), 'selected_tool_identity_changed')
        receipt.update(status=receipt['help']['status'],capability_available=receipt['help']['capability_available'])
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError) as error:
        receipt['error_type']=type(error).__name__
        if isinstance(error,CapabilityError): receipt['error_guard']=str(error)
        receipt.update(status='unavailable',capability_available=False)
    finally:
        try:
            need(set(private.iterdir())=={entry[0] for entry in owned},'private_output_membership_changed')
            for path,device,inode,size,value in owned:
                info=path.lstat()
                need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and (info.st_dev,info.st_ino,info.st_size)==
                     (device,inode,size) and digest(path.read_bytes())==value,'private_output_ownership_changed')
            for path,*_ in owned: path.unlink()
            private.rmdir();receipt['owned_private_output_removed']=not private.exists()
        except (OSError,ValueError) as error:
            receipt.update(owned_private_output_removed=False,status='unavailable',capability_available=False,
                           cleanup_error_type=type(error).__name__)
        receipt.update(finished_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                       elapsed_seconds=round(time.monotonic()-started,2),private_bytes_captured=total)
        descriptor=os.open(output/'receipt.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'w') as target: json.dump(receipt,target,indent=2,sort_keys=True);target.write('\n')
    return receipt


def main():
    if len(sys.argv)!=1:
        print('Capability discovery takes no app, device, command or output argument.',file=sys.stderr);return 2
    try: receipt=collect()
    except (OSError,ValueError) as error:
        print(json.dumps({'status':'unavailable','error_type':type(error).__name__}));return 2
    print(json.dumps({key:receipt[key] for key in ('status','capability_available','subsequent_appinfo_ready',
                                                 'appinfo_output_schema_observed','owned_private_output_removed')}))
    return 0 if receipt['capability_available'] and receipt['owned_private_output_removed'] else 2


if __name__=='__main__':
    sys.exit(main())
