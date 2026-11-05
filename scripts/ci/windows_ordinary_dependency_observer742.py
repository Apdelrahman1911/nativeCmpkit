# SPDX-License-Identifier: Apache-2.0
"""Stage A: finite public text observations, NEVER dependency/native admission.

This controller does not invoke the wrapper, Gradle, Java, Rust, JAR/ZIP tooling,
policy writers, key import, verification-metadata bootstrap, or any library test.
A single Python worker receives GO only after an owned Windows Job assignment.
All signatures/checksums are untrusted observations; Stage B requires independent
provenance, real two-root policies/closure and the existing release/native gates.
"""
from __future__ import annotations

import argparse
import ast
import base64
import ctypes
import hashlib
import http.client
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import stat
import subprocess
import sys
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PLAN = 'scripts/ci/windows-ordinary-observation742-plan.json'
PLAN_SHA256 = 'e3d86c27cbb88650b306410c01a07b094c8166552f45f8b5ef1718b0cfaf5133'
OUTPUT = 'build/ci-verification/windows-ordinary-observation742'
CHOICE = 'windows-ordinary-dependency-observation1'
REPOSITORY = 'Apdelrahman1911/nativeCmpkit'
REF = 'refs/heads/development/javafx-ordinary-consumer1'
TOTAL_SECONDS = 600
CLEANUP_SECONDS = 30
ACQUISITION_SECONDS = 480
IO_SECONDS = 20
MAX_REQUESTS = 128
MAX_BODY = 2 * 1024 * 1024
MAX_TOTAL_BODY = 64 * 1024 * 1024
MAX_CAPTURE = 1024 * 1024
SOURCE_LIMIT = 1024 * 1024
SOURCE_FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
ORIGINS = {
    'central': 'https://repo.maven.apache.org/maven2/',
    'google': 'https://dl.google.com/dl/android/maven2/',
    'plugin-portal': 'https://plugins.gradle.org/m2/',
}
KINDS = ('pom', 'pom.sha256', 'pom.asc', 'module', 'module.sha256', 'module.asc')
NO_ADMISSION = {
    'observations_are_untrusted': True,
    'signature_cryptographically_verified': False,
    'same_registry_checksum_is_independent_security_certification': False,
    'publisher_provenance_qualified': False,
    'resolved_graph_complete': False,
    'dependency_or_bootstrap_execution_admitted': False,
    'strict_two_root_policy_qualified': False,
    'staged_primary_payloads_qualified': False,
    'native_or_ordinary_consumer_qualified': False,
    'security_legal_or_release_readiness': False,
    'publication_or_issue_closure': False,
    'reviewed_expectations_authority': None,
}


class ObservationRefusal(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise ObservationRefusal(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def bounded_time(deadline, message, clock=time.monotonic):
    remaining = deadline - clock()
    if remaining <= 0:
        raise TimeoutError(message)
    return remaining


def relative_path(relative):
    need(type(relative) is str and 0 < len(relative) <= 240 and '\\' not in relative and ':' not in relative,
         'Only bounded exact relative source/output paths')
    path = PurePosixPath(relative)
    need(not path.is_absolute() and path.as_posix() == relative and
         all(part not in ('', '.', '..') for part in path.parts), 'No traversal/path aliases')
    return path


def directory_pin(path):
    need(path.is_absolute() and path.resolve(strict=True) == path, 'Owned/source directory alias refused')
    info = path.lstat()
    need(stat.S_ISDIR(info.st_mode) and not info.st_mode & stat.S_IFLNK and
         not getattr(info, 'st_file_attributes', 0) & 1024, 'Directory link/reparse refused')
    return (info.st_dev, info.st_ino, info.st_mode, getattr(info, 'st_file_attributes', 0))


def parents_pins(root, path):
    need(path.is_relative_to(root), 'Path outside the exact source root')
    result = {root: directory_pin(root)}
    current = root
    for part in path.relative_to(root).parts[:-1]:
        current = current / part
        result[current] = directory_pin(current)
    return result


WIN32_SOURCE_FIELDS = ('volume_serial_64', 'file_id_128', 'file_attributes', 'number_of_links',
                       'file_size', 'creation_time_100ns', 'last_write_time_100ns', 'change_time_100ns')


def source_stat_identity(info):
    return tuple(getattr(info, field) for field in SOURCE_FIELDS)


def require_identity(actual, expected, fields, message, relative):
    need(len(actual) == len(expected) == len(fields), 'Exact complete identity view required')
    different = [field for field, current, old in zip(fields, actual, expected) if current != old]
    need(not different, message + ': ' + relative + ' [' + ','.join(different) + ']')


def require_source_shape(info, limit, allow_empty=False):
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
         (0 <= info.st_size if allow_empty else 0 < info.st_size) and info.st_size <= limit and
         not getattr(info, 'st_file_attributes', 0) & 1024,
         'Only bounded unshared ordinary source/evidence')


class _Win32FileIdentity:
    """Same native view for named no-reparse handles and borrowed CRT handles.

    Required FileIdInfo18 retains all 128 ID bits and the 64-bit volume number.
    FileBasicInfo0/StandardInfo1 retain complete owning metadata, not the
    potentially different CPython named-stat and CRT-fstat representations.
    No unsupported-query fallback, timestamp truncation or descriptor ownership
    transfer is admitted. This is custody, not a general OS/security sandbox.
    """
    class BasicInfo(ctypes.Structure):
        _fields_ = [('CreationTime', ctypes.c_int64), ('LastAccessTime', ctypes.c_int64),
                    ('LastWriteTime', ctypes.c_int64), ('ChangeTime', ctypes.c_int64),
                    ('FileAttributes', ctypes.c_uint32)]

    class StandardInfo(ctypes.Structure):
        _fields_ = [('AllocationSize', ctypes.c_int64), ('EndOfFile', ctypes.c_int64),
                    ('NumberOfLinks', ctypes.c_uint32), ('DeletePending', ctypes.c_ubyte),
                    ('Directory', ctypes.c_ubyte)]

    class IdInfo(ctypes.Structure):
        _fields_ = [('VolumeSerialNumber', ctypes.c_uint64), ('FileId', ctypes.c_ubyte * 16)]

    def __init__(self):
        import msvcrt
        self.get_osfhandle = msvcrt.get_osfhandle
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        need((ctypes.sizeof(self.BasicInfo), ctypes.sizeof(self.StandardInfo), ctypes.sizeof(self.IdInfo)) ==
             (40, 24, 24), 'Exact Windows native metadata ABI required')
        self.api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.api.CreateFileW.restype = ctypes.c_void_p
        self.api.GetFileType.argtypes, self.api.GetFileType.restype = [ctypes.c_void_p], ctypes.c_uint32
        self.api.GetFileInformationByHandleEx.argtypes = [ctypes.c_void_p, ctypes.c_int32,
                                                        ctypes.c_void_p, ctypes.c_uint32]
        self.api.GetFileInformationByHandleEx.restype = ctypes.c_int32
        self.api.CloseHandle.argtypes, self.api.CloseHandle.restype = [ctypes.c_void_p], ctypes.c_int32

    def query(self, handle, limit, allow_empty=False):
        need(type(handle) is int and handle > 0 and handle != ctypes.c_void_p(-1).value,
             'Exact live owning or borrowed native file handle required')
        need(self.api.GetFileType(handle) == 1, 'Only ordinary disk file handles')
        basic, standard, identifier = self.BasicInfo(), self.StandardInfo(), self.IdInfo()
        for information_class, value in ((0, basic), (1, standard), (18, identifier)):
            need(self.api.GetFileInformationByHandleEx(handle, information_class, ctypes.byref(value),
                                                      ctypes.sizeof(value)) != 0,
                 'Required full Win32 metadata query failed: ' + str(information_class))
        attributes, size = int(basic.FileAttributes), int(standard.EndOfFile)
        need(not attributes & (0x400 | 0x10) and standard.Directory == 0 and standard.DeletePending == 0 and
             standard.NumberOfLinks == 1 and (0 <= size if allow_empty else 0 < size) and size <= limit,
             'Native reparse/directory/deleting/shared/bounded file guard')
        need(basic.CreationTime >= 0 and basic.LastWriteTime >= 0 and basic.ChangeTime >= 0,
             'Complete nonnegative native file times')
        return (int(identifier.VolumeSerialNumber), int.from_bytes(bytes(identifier.FileId), 'little'),
                attributes, int(standard.NumberOfLinks), size, int(basic.CreationTime),
                int(basic.LastWriteTime), int(basic.ChangeTime))

    def close_owned(self, handle, primary=None):
        try:
            need(self.api.CloseHandle(handle) != 0, 'Owned native metadata handle close failed')
        except BaseException as error:
            if primary is None:
                raise
            primary.add_note('Owned metadata-handle close refusal: ' + type(error).__name__)

    def named(self, path, limit, allow_empty=False):
        text = os.fspath(path)
        need(type(text) is str and 0 < len(text) <= 4096 and path.is_absolute(),
             'Exact bounded absolute source/evidence metadata path')
        # FILE_READ_ATTRIBUTES; share read/write/delete; OPEN_EXISTING.
        # OPEN_REPARSE_POINT applies to the final path and BACKUP_SEMANTICS lets
        # the queried regular/directory guard reject rather than follow aliases.
        handle = self.api.CreateFileW(text, 0x80, 0x7, None, 3, 0x00200000 | 0x02000000, None)
        need(type(handle) is int and handle > 0 and handle != ctypes.c_void_p(-1).value,
             'Owned native metadata handle open failed')
        try:
            identity = self.query(handle, limit, allow_empty)
        except BaseException as primary:
            self.close_owned(handle, primary)
            raise
        self.close_owned(handle)
        return identity

    def borrowed(self, descriptor, limit, allow_empty=False):
        # get_osfhandle borrows the CRT descriptor's handle. Never CloseHandle
        # this value: the enclosing fdopen context alone owns descriptor close.
        return self.query(self.get_osfhandle(descriptor), limit, allow_empty)


def _read_windows_regular(root, relative, limit=SOURCE_LIMIT, allow_empty=False):
    path = root.joinpath(*relative_path(relative).parts)
    parents = parents_pins(root, path)
    old = path.lstat()
    require_source_shape(old, limit, allow_empty)
    named_stat = source_stat_identity(old)
    native = _Win32FileIdentity()
    identity = native.named(path, limit, allow_empty)
    need(identity[3:5] == (old.st_nlink, old.st_size), 'Named native link/size custody')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require_source_shape(opened, limit, allow_empty)
        descriptor_stat = source_stat_identity(opened)
        need((opened.st_nlink, opened.st_size) == (old.st_nlink, old.st_size), 'Opened source link/size custody')
        require_identity(native.borrowed(stream.fileno(), limit, allow_empty), identity, WIN32_SOURCE_FIELDS,
                         'Opened native source identity drift', relative)
        payload = stream.read(limit + 1)
        require_identity(source_stat_identity(os.fstat(stream.fileno())), descriptor_stat, SOURCE_FIELDS,
                         'Read descriptor-stat source identity drift', relative)
        require_identity(native.borrowed(stream.fileno(), limit, allow_empty), identity, WIN32_SOURCE_FIELDS,
                         'Read native source identity drift', relative)
        require_identity(source_stat_identity(path.lstat()), named_stat, SOURCE_FIELDS,
                         'Read named-stat source identity drift', relative)
        require_identity(native.named(path, limit, allow_empty), identity, WIN32_SOURCE_FIELDS,
                         'Read named-native source identity drift', relative)
    fresh = path.lstat()
    require_source_shape(fresh, limit, allow_empty)
    require_identity(source_stat_identity(fresh), named_stat, SOURCE_FIELDS, 'Closed named-stat source identity drift', relative)
    require_identity(native.named(path, limit, allow_empty), identity, WIN32_SOURCE_FIELDS,
                     'Closed named-native source identity drift', relative)
    need(len(payload) == old.st_size, 'Exact complete source/evidence payload size')
    need(all(directory_pin(parent) == pin for parent, pin in parents.items()), 'Source ancestor identity drift')
    return payload, {'bytes': len(payload), 'sha256': digest(payload), 'mode': format(stat.S_IMODE(old.st_mode), '04o'),
                     'stat_identity': list(named_stat), 'descriptor_stat_identity': list(descriptor_stat),
                     'windows_file_identity': {'view': 'Win32-FileBasic0-Standard1-Id18-v1',
                                               'fields': list(WIN32_SOURCE_FIELDS),
                                               'values': [str(value) for value in identity]}}


def read_regular(root, relative, limit=SOURCE_LIMIT):
    if os.name == 'nt':
        return _read_windows_regular(root, relative, limit)
    path = root.joinpath(*relative_path(relative).parts)
    parents = parents_pins(root, path)
    old = path.lstat()
    identity = tuple(getattr(old, field) for field in SOURCE_FIELDS)
    need(stat.S_ISREG(old.st_mode) and old.st_nlink == 1 and 0 < old.st_size <= limit and
         not getattr(old, 'st_file_attributes', 0) & 1024, 'Only bounded unshared ordinary source/evidence')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as stream:
        need(tuple(getattr(os.fstat(stream.fileno()), field) for field in SOURCE_FIELDS) == identity,
             'Opened source identity drift')
        payload = stream.read(limit + 1)
        need(tuple(getattr(os.fstat(stream.fileno()), field) for field in SOURCE_FIELDS) == identity,
             'Read source identity drift')
    fresh = path.lstat()
    need(tuple(getattr(fresh, field) for field in SOURCE_FIELDS) == identity and len(payload) == old.st_size,
         'Closed source identity drift')
    need(all(directory_pin(parent) == pin for parent, pin in parents.items()), 'Source ancestor identity drift')
    return payload, {'bytes': len(payload), 'sha256': digest(payload), 'mode': format(stat.S_IMODE(old.st_mode), '04o'),
                     'stat_identity': list(identity)}


def strict_json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'Duplicate JSON member')
            result[key] = value
        return result
    def constant(_value):
        raise ObservationRefusal('Nonfinite JSON value')
    need(type(payload) is bytes and 0 < len(payload) <= SOURCE_LIMIT * 2, 'Bounded JSON payload required')
    value = json.loads(payload.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=constant)
    work = [(value, 0)]
    nodes = 0
    while work:
        item, depth = work.pop()
        nodes += 1
        need(nodes <= 32768 and depth <= 128, 'Finite JSON structure required')
        if isinstance(item, dict):
            work.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            work.extend((child, depth + 1) for child in item)
        elif isinstance(item, float):
            need(math.isfinite(item), 'Nonfinite JSON number')
    return value


def load_plan(root):
    raw, identity = read_regular(root, PLAN)
    need(identity['sha256'] == PLAN_SHA256, 'The owning fixed observation plan changed')
    plan = strict_json(raw)
    need(plan.get('schema') == 'nativecmpkit-Windows-observation-plan742-r1' and
         plan.get('choice') == CHOICE and plan.get('repository') == REPOSITORY and plan.get('ref') == REF and
         plan.get('limits') == {'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
             'acquisition_seconds': ACQUISITION_SECONDS, 'io_seconds': IO_SECONDS, 'max_requests': MAX_REQUESTS,
             'max_body_bytes': MAX_BODY, 'max_total_body_bytes': MAX_TOTAL_BODY, 'max_capture_bytes': MAX_CAPTURE} and
         plan.get('no_admission') == NO_ADMISSION and plan.get('archive_reuse') == [],
         'Exact source recipe/finite bounds/no trust promotion required')
    seeds = plan.get('seeds')
    need(type(seeds) is list and 0 < len(seeds) <= 21 and len({seed['id'] for seed in seeds}) == len(seeds),
         'Exact finite repository-qualified seed set')
    expanded = []
    for seed in seeds:
        need(set(seed) == {'id', 'repository', 'group', 'module', 'version', 'source_literals', 'derivation'},
             'Exact declared seed schema')
        need(type(seed['source_literals']) is list and seed['source_literals'], 'A seed needs held source literals')
        for literal in seed['source_literals']:
            need(set(literal) == {'path', 'text'} and literal['path'] in plan['source_bindings'] and
                 type(literal['text']) is str and 0 < len(literal['text']) <= 240, 'Finite held literal source')
        for kind in KINDS:
            url = coordinate_url(seed, kind)
            expanded.append({'id': f"{seed['id']}:{kind}", 'seed': seed['id'], 'kind': kind, 'url': url})
    need(plan.get('requests') == expanded and len(expanded) <= MAX_REQUESTS and
         len({row['url'] for row in expanded}) == len(expanded), 'Only exact source-derived unique request URLs')
    return plan, identity


def coordinate_url(seed, kind):
    need(seed.get('repository') in ORIGINS and kind in KINDS, 'Unknown source repository or file type')
    for field in ('group', 'module', 'version'):
        value = seed.get(field)
        need(type(value) is str and 0 < len(value) <= 120 and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._+-]*', value) and
             '..' not in value and not value.upper().endswith('SNAPSHOT') and
             not any(token in value for token in ('LATEST', 'RELEASE', '+', '[', ']', '(', ')', '$')),
             'Only fixed exact Maven coordinates; no dynamic/property/interpolation graph')
    need(all(part for part in seed['group'].split('.')), 'Empty group segment')
    url = (ORIGINS[seed['repository']] + seed['group'].replace('.', '/') + '/' + seed['module'] + '/' +
           seed['version'] + '/' + seed['module'] + '-' + seed['version'] + '.' + kind)
    parsed = urllib.parse.urlsplit(url)
    need(parsed.scheme == 'https' and parsed.hostname in {'repo.maven.apache.org', 'dl.google.com', 'plugins.gradle.org'} and
         parsed.port is None and parsed.username is None and parsed.password is None and
         not parsed.query and not parsed.fragment and '%' not in parsed.path, 'Exact public HTTPS origin/path required')
    return url


def validate_request(row, plan):
    need(type(row) is dict and row in plan['requests'], 'No caller URL, recursive graph or arbitrary request')
    original = [entry for entry in plan['requests'] if entry['id'] == row['id']]
    need(len(original) == 1 and original[0] == row, 'Only an exact owning request row')
    seed = [entry for entry in plan['seeds'] if entry['id'] == row['seed']]
    need(len(seed) == 1 and coordinate_url(seed[0], row['kind']) == row['url'], 'Request/source coordinate mismatch')
    return urllib.parse.urlsplit(row['url'])


def restore_diagnostic_workflow770(workflow):
    """Only the exact diagnostic route inverse; all original checks remain fresh."""
    need(type(workflow) is bytes and len(workflow) <= SOURCE_LIMIT, 'Bounded exact owning workflow bytes')
    marker = b'  # One-request diagnostic770: original120 is not replayed; no dependency admission.\n'
    if marker not in workflow:
        return workflow
    need(workflow.count(marker) == 1, 'One exact appended diagnostic job770')
    prefix, suffix = workflow.split(marker)
    need(len(marker + suffix) == 1509 and digest(marker + suffix) == '7dae7cfcbee6b5e687efdc7c2cd30a3b7854afea356336afc98895b025555bcf',
         'Exact diagnostic job body; no altered permissions, acquisition or exports')
    before = b'        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1, windows-ordinary-dependency-observation1]'
    after = b'        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1, windows-ordinary-dependency-observation1, windows-observer-one-request-diagnostic1]'
    need(prefix.count(after) == 1 and before not in prefix, 'One exact added diagnostic manual choice')
    restored = prefix.replace(after, before)
    need(len(restored) == 13748 and digest(restored) == '5f5b2ed46adaf900f157d5dab37b04087226ecd27e1cedbec88912999d574a9f',
         'Diagnostic inverse must restore all original native, Stop, ordinary and120 bodies')
    return restored


def snapshot_sources(root, plan, clock=time.monotonic, deadline=None):
    rows = {}
    for relative, expected in plan['source_bindings'].items():
        if deadline is not None:
            bounded_time(deadline, 'Source custody exhausted shared allocation', clock)
        raw, row = read_regular(root, relative)
        need(set(expected) == {'bytes', 'sha256'} and (row['bytes'], row['sha256']) ==
             (expected['bytes'], expected['sha256']), 'Held source prerequisite changed: ' + relative)
        rows[relative] = row
        for seed in plan['seeds']:
            for literal in seed['source_literals']:
                if literal['path'] == relative:
                    need(literal['text'].encode('utf-8') in raw, 'Exact declared seed source literal changed')
        if relative == 'scripts/ci/javafx_ordinary_maven_consumer.py':
            assignments = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign) and
                           any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256'
                               for target in node.targets)]
            need(len(assignments) == 1 and isinstance(assignments[0].value, ast.Constant) and
                 assignments[0].value.value is None, 'Production expectation authority must remain None')
    workflow, workflow_row = read_regular(root, '.github/workflows/javafx-library-candidate.yml')
    workflow = restore_diagnostic_workflow770(workflow)
    recipe = plan['workflow_preservation']
    marker = recipe['suffix_marker'].encode('utf-8')
    need(workflow.count(marker) == 1, 'Only the independent appended observational job')
    prefix, suffix = workflow.split(marker)
    need(digest(marker + suffix) == recipe['suffix_sha256'], 'Independent observation job source changed')
    old, new = recipe['options_before'].encode(), recipe['options_after'].encode()
    need(prefix.count(new) == 1, 'One exact manual observation option, no native condition change')
    original = prefix.replace(new, old)
    need(len(original) == recipe['original_bytes'] and digest(original) == recipe['original_sha256'],
         'Original native/public Stop and ordinary job bodies/conditions must remain exact')
    rows['.github/workflows/javafx-library-candidate.yml'] = workflow_row
    raw, plan_row = read_regular(root, PLAN)
    need(plan_row['sha256'] == PLAN_SHA256, 'Plan changed during source custody')
    rows[PLAN] = plan_row
    own_relative = 'scripts/ci/windows_ordinary_dependency_observer742.py'
    rows[own_relative] = read_regular(root, own_relative)[1]
    return rows


def validate_public_text(kind, payload, filename):
    need(type(payload) is bytes and 0 < len(payload) <= MAX_BODY, 'Only bounded complete response text')
    if kind.endswith('.sha256'):
        need(len(payload) <= 512, 'Bounded checksum text')
        match = re.fullmatch(rb'([0-9a-fA-F]{64})(?:[ \t]+\*?([A-Za-z0-9._+-]{1,200}))?[ \t]*(?:\r?\n)?', payload)
        need(match is not None and (match.group(2) is None or match.group(2).decode('ascii') == filename[:-7]),
             'Exact ASCII SHA256 and optional owning descriptor filename')
        return {'advertised_sha256': match.group(1).decode('ascii').lower(), 'checksum_is_untrusted': True}
    if kind.endswith('.asc'):
        need(len(payload) <= 128 * 1024, 'Bounded ASCII armored signature')
        text = payload.decode('ascii', 'strict').replace('\r\n', '\n')
        need('\r' not in text and text.endswith('\n'), 'Canonical complete signature armor lines')
        lines = text.splitlines()
        need(lines and lines[0] == '-----BEGIN PGP SIGNATURE-----' and lines[-1] == '-----END PGP SIGNATURE-----',
             'Detached signature armor only, not keys/messages/binary packets')
        index = 1
        while index < len(lines) - 1 and lines[index]:
            need(re.fullmatch(r'(?:Version|Comment): [\x20-\x7e]{1,200}', lines[index]) is not None,
                 'Only bounded standard signature armor headers')
            index += 1
        need(index < len(lines) - 2 and lines[index] == '', 'Signature armor needs a body separator')
        body = lines[index + 1:-1]
        crc = body[-1] if body and body[-1].startswith('=') else None
        if crc:
            need(re.fullmatch(r'=[A-Za-z0-9+/]{4}', crc) is not None, 'ASCII armor checksum syntax')
            body = body[:-1]
        need(body and len(body) <= 2048 and all(re.fullmatch(r'[A-Za-z0-9+/]{1,76}={0,2}', line) for line in body),
             'Bounded ASCII base64 signature body')
        decoded = base64.b64decode(''.join(body), validate=True)
        need(0 < len(decoded) <= 65536, 'Bounded signature bytes')
        if crc:
            value = 0xB704CE
            for octet in decoded:
                value ^= octet << 16
                for _ in range(8):
                    value <<= 1
                    if value & 0x1000000:
                        value ^= 0x1864CFB
            need(base64.b64decode(crc[1:], validate=True) == (value & 0xFFFFFF).to_bytes(3, 'big'),
                 'ASCII armor checksum mismatch')
        return {'armored_signature_syntax_only': True, 'decoded_signature_bytes': len(decoded),
                'signature_cryptographically_verified': False, 'publisher_provenance_qualified': False}
    text = payload.decode('utf-8', 'strict')
    need(not re.search('[\x00-\x08\x0b\x0c\x0e-\x1f]', text), 'Binary/control response is not public descriptor text')
    if kind == 'pom':
        need(not re.search(r'<!\s*(?:DOCTYPE|ENTITY)', text, re.I), 'DTD/entities refused before XML parsing')
        document = ET.fromstring(text)
        namespace = '{http://maven.apache.org/POM/4.0.0}' if document.tag.startswith('{') else ''
        need(document.tag == namespace + 'project' and document.findtext(namespace + 'modelVersion') == '4.0.0',
             'An actual Maven POM project/modelVersion, never HTML or an error document')
        work, count = [(document, 0)], 0
        while work:
            node, depth = work.pop()
            count += 1
            need(count <= 32768 and depth <= 128, 'Finite XML structure')
            work.extend((child, depth + 1) for child in node)
        return {'descriptor_syntax_only': True, 'descriptor_kind': 'pom', 'xml_element_count': count,
                'resolved_graph_complete': False}
    need(kind == 'module', 'Unknown public text type')
    document = strict_json(payload)
    component = document.get('component') if type(document) is dict else None
    need(type(document) is dict and document.get('formatVersion') == '1.1' and type(component) is dict and
         all(type(component.get(key)) is str and 0 < len(component[key]) <= 240 for key in ('group', 'module', 'version')),
         'Actual Gradle module descriptor/component syntax only')
    return {'descriptor_syntax_only': True, 'descriptor_kind': 'module', 'resolved_graph_complete': False}


class NetworkBudget:
    def __init__(self, deadline, clock=time.monotonic):
        self.deadline = deadline
        self.clock = clock
        self.requests = 0
        self.body_bytes = 0

    def start(self):
        bounded_time(self.deadline, 'Finite acquisition deadline exhausted', self.clock)
        need(self.requests < MAX_REQUESTS, 'Maximum exact request count reached')
        self.requests += 1
        return min(self.deadline, self.clock() + IO_SECONDS)

    def receive(self, count):
        need(type(count) is int and count >= 0 and self.body_bytes + count <= MAX_TOTAL_BODY,
             'Shared64MiB raw body bound exceeded')
        self.body_bytes += count


def observe_one(row, plan, budget, connection_factory=None):
    parsed = validate_request(row, plan)
    started = budget.clock()
    deadline = budget.start()
    result = dict(row, status='refused', body_bytes=0, body_sha256=None, complete_response=False,
                  public_text_qualified=False, exception_type=None)
    connection = response = transport = None
    body = bytearray()
    try:
        factory = connection_factory or http.client.HTTPSConnection
        # http.client never consults proxy environment/registry, auth or cookie
        # handlers and does not follow any redirect. Only fixed origin/path GET.
        connection = factory(parsed.hostname, port=443, timeout=min(IO_SECONDS, bounded_time(deadline, 'Request timeout', budget.clock)),
                             context=ssl.create_default_context())
        connection.connect()
        transport = connection.sock
        need(transport is not None, 'Exact HTTPS connection required')
        transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request connect budget', budget.clock)))
        connection.request('GET', parsed.path, body=None, headers={'Accept': 'application/xml, application/json, text/plain, application/pgp-signature',
            'Accept-Encoding': 'identity', 'Connection': 'close', 'User-Agent': 'NativeCmpKit-StageA-TextObserver742/1'})
        transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request headers budget', budget.clock)))
        response = connection.getresponse()
        result['http_status'] = response.status
        need(type(response.status) is int and response.status == 200,
             'Every redirect and non200 response is refused; no fallback or retry')
        headers = response.getheaders()
        need(len(headers) <= 64 and sum(len(key) + len(value) for key, value in headers) <= 16384,
             'Bounded public response headers')
        lengths = [value for key, value in headers if key.lower() == 'content-length']
        encodings = [value for key, value in headers if key.lower() == 'content-encoding']
        need(len(lengths) <= 1 and len(encodings) <= 1 and (not encodings or encodings[0].lower() == 'identity'),
             'No duplicate length or compressed response body')
        declared = None
        if lengths:
            need(re.fullmatch('[0-9]{1,10}', lengths[0]) is not None, 'Exact bounded Content-Length')
            declared = int(lengths[0])
            need(0 < declared <= MAX_BODY, 'Response advertised body bound')
        while True:
            remaining = bounded_time(deadline, 'Request body budget', budget.clock)
            # read1 may release the owning response fp and its borrowed socket.
            # Closed lifetime skips only settimeout: still read EOF, keep caps,
            # framing/declared-length checks and the shared deadline unchanged.
            if not response.isclosed():
                transport.settimeout(min(IO_SECONDS, remaining))
            room = min(MAX_BODY - len(body), MAX_TOTAL_BODY - budget.body_bytes)
            # Never read a probing byte past either hard cap. A response that
            # exactly exhausts a cap before EOF is conservatively refused.
            need(room > 0, 'No remaining bounded raw body capacity')
            chunk = response.read1(min(65536, room))
            need(type(chunk) is bytes, 'Binary transport bytes required')
            if not chunk:
                break
            budget.receive(len(chunk))
            body.extend(chunk)
            need(len(body) <= MAX_BODY, 'Response body2MiB cap exceeded')
        bounded_time(deadline, 'Measured request total exceeded20s', budget.clock)
        need(declared is None or declared == len(body), 'Partial/mismatched declared response')
        result['complete_response'] = True
        filename = parsed.path.rsplit('/', 1)[1]
        details = validate_public_text(row['kind'], bytes(body), filename)
        result.update(details, status='observed', public_text_qualified=True)
    except (ObservationRefusal, OSError, TimeoutError, UnicodeError, ValueError, RecursionError, OverflowError, ET.ParseError, http.client.HTTPException) as error:
        result['exception_type'] = type(error).__name__
    finally:
        close_errors = []
        for resource, name in ((response, 'response'), (connection, 'connection')):
            if resource is not None:
                try:
                    resource.close()
                except (OSError, http.client.HTTPException) as error:
                    close_errors.append({'resource': name, 'exception_type': type(error).__name__})
        result.update(body_bytes=len(body), body_sha256=digest(body) if body else None,
                      elapsed_seconds=budget.clock() - started, close_errors=close_errors,
                      all_redirects_refused=True, credential_cookie_proxy_inheritance=False,
                      signature_cryptographically_verified=False, publisher_provenance_qualified=False)
        if close_errors:
            result.update(status='refused', public_text_qualified=False)
    return result, bytes(body)


def create_owned(path, parent_pins):
    parent = path.parent
    need(parent in parent_pins and directory_pin(parent) == parent_pins[parent], 'Fresh owned directory parent custody')
    path.mkdir(mode=0o700)
    parent_pins[path] = directory_pin(path)
    need(directory_pin(parent) == parent_pins[parent], 'Owned directory creation parent drift')


def _write_windows_exclusive(root, relative, payload, pins):
    path = root.joinpath(*relative_path(relative).parts)
    parent = path.parent
    need(parent in pins and directory_pin(parent) == pins[parent], 'Owned output ancestor identity')
    native = _Win32FileIdentity()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(payload) == len(payload), 'Exact complete exclusive write')
        stream.flush()
        os.fsync(stream.fileno())
        opened = os.fstat(stream.fileno())
        require_source_shape(opened, MAX_BODY + SOURCE_LIMIT, allow_empty=True)
        need(opened.st_size == len(payload), 'Exclusive write size')
        descriptor_stat = source_stat_identity(opened)
        named = path.lstat()
        require_source_shape(named, MAX_BODY + SOURCE_LIMIT, allow_empty=True)
        named_stat = source_stat_identity(named)
        need(named.st_size == len(payload), 'Exclusive named write size')
        identity = native.borrowed(stream.fileno(), MAX_BODY + SOURCE_LIMIT, allow_empty=True)
        require_identity(native.named(path, MAX_BODY + SOURCE_LIMIT, allow_empty=True), identity, WIN32_SOURCE_FIELDS,
                         'Exclusive opened native/path identity drift', relative)
        require_identity(source_stat_identity(os.fstat(stream.fileno())), descriptor_stat, SOURCE_FIELDS,
                         'Exclusive descriptor-stat identity drift', relative)
        require_identity(source_stat_identity(path.lstat()), named_stat, SOURCE_FIELDS,
                         'Exclusive named-stat identity drift', relative)
        require_identity(native.borrowed(stream.fileno(), MAX_BODY + SOURCE_LIMIT, allow_empty=True), identity,
                         WIN32_SOURCE_FIELDS, 'Exclusive descriptor-native identity drift', relative)
    # Windows may finalize last-write/change timestamps at owning writer close.
    # This explicit self-write interval is not a source-read drift waiver:
    # every non-time field stays exact, times cannot move backwards, and the
    # permitted time deltas do not identify an actor or establish intrinsic cause.
    # closed payload is reopened read-only with full final path+descriptor+native
    # before/after custody and exact byte-for-byte content readback.
    final_payload, final = _read_windows_regular(root, relative, MAX_BODY + SOURCE_LIMIT, allow_empty=True)
    need(final_payload == payload and final['sha256'] == digest(payload), 'Exclusive final complete content readback')
    final_native = tuple(int(value) for value in final['windows_file_identity']['values'])
    final_stat = tuple(final['stat_identity'])
    native_non_time = tuple(field for field in WIN32_SOURCE_FIELDS
                            if field not in ('last_write_time_100ns', 'change_time_100ns'))
    native_indices = [WIN32_SOURCE_FIELDS.index(field) for field in native_non_time]
    require_identity(tuple(final_native[index] for index in native_indices), tuple(identity[index] for index in native_indices),
                     native_non_time, 'Exclusive owning-close non-time native identity drift', relative)
    stat_non_time = tuple(field for field in SOURCE_FIELDS if field not in ('st_mtime_ns', 'st_ctime_ns'))
    stat_indices = [SOURCE_FIELDS.index(field) for field in stat_non_time]
    require_identity(tuple(final_stat[index] for index in stat_indices), tuple(named_stat[index] for index in stat_indices),
                     stat_non_time, 'Exclusive owning-close non-time named-stat drift', relative)
    need(all(final_native[index] >= identity[index] for index in (6, 7)) and
         all(final_stat[index] >= named_stat[index] for index in (5, 6)), 'Owning write-close time moved backwards')
    need(directory_pin(parent) == pins[parent], 'Evidence close/path/parent drift')
    changed_native = [WIN32_SOURCE_FIELDS[index] for index in (6, 7) if final_native[index] != identity[index]]
    changed_named = [SOURCE_FIELDS[index] for index in (5, 6) if final_stat[index] != named_stat[index]]
    return {'path': relative, 'bytes': len(payload), 'sha256': digest(payload),
            'windows_write_close_custody': {
                'only_forward_time_fields_changed_across_owning_close_interval': True,
                'forward_time_transition_does_not_establish_actor_or_cause': True,
                'changed_native_time_fields': changed_native, 'changed_named_time_fields': changed_named,
                'before_close_native_values': [str(value) for value in identity],
                'final_closed_native_values': [str(value) for value in final_native],
                'before_close_named_stat7': [str(value) for value in named_stat],
                'before_close_descriptor_stat7': [str(value) for value in descriptor_stat],
                'final_closed_named_stat7': [str(value) for value in final_stat],
                'full_final_path_descriptor_native_custody': True,
                'exact_final_complete_content_readback': True}}


def write_exclusive(root, relative, payload, pins):
    need(type(payload) is bytes and len(payload) <= MAX_BODY + SOURCE_LIMIT, 'Bounded exclusive evidence')
    if os.name == 'nt':
        return _write_windows_exclusive(root, relative, payload, pins)
    path = root.joinpath(*relative_path(relative).parts)
    parent = path.parent
    need(parent in pins and directory_pin(parent) == pins[parent], 'Owned output ancestor identity')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        if os.name != 'nt':
            os.fchmod(stream.fileno(), 0o600)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == len(payload), 'Exclusive write identity')
        identity = tuple(getattr(info, field) for field in SOURCE_FIELDS)
    need(tuple(getattr(path.lstat(), field) for field in SOURCE_FIELDS) == identity and
         directory_pin(parent) == pins[parent], 'Evidence close/path/parent drift')
    return {'path': relative, 'bytes': len(payload), 'sha256': digest(payload)}


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def annotate_checksum_agreement(results):
    by_id = {row['id']: row for row in results}
    for row in results:
        if row['kind'].endswith('.sha256') and row.get('public_text_qualified'):
            primary = by_id.get(row['id'][:-7])
            row['advertised_descriptor_digest_agrees'] = bool(primary and primary.get('public_text_qualified') and
                primary.get('body_sha256') == row.get('advertised_sha256'))
            row['same_registry_checksum_is_independent_security_certification'] = False


def verify_worker_job(handle):
    # An externally invoked --worker plus a guessed GO must not be enough.
    # The child inherits only the owning unnamed Job handle and verifies exact
    # current-process membership, the resource limits and single active child.
    from ctypes import wintypes
    need(os.name == 'nt' and type(handle) is int and handle > 0, 'Exact inherited owned Job handle')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetCurrentProcess.argtypes, api.GetCurrentProcess.restype = [], wintypes.HANDLE
    api.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    api.IsProcessInJob.restype = wintypes.BOOL
    api.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    api.QueryInformationJobObject.restype = wintypes.BOOL
    inside = wintypes.BOOL()
    need(api.IsProcessInJob(api.GetCurrentProcess(), handle, ctypes.byref(inside)) and inside.value,
         'Actual worker membership in the inherited owning Job')
    class BasicLimits(ctypes.Structure):
        _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong),
            ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t),
            ('ActiveProcessLimit', wintypes.DWORD), ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]
    class IOCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
            'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]
    class ExtendedLimits(ctypes.Structure):
        _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', IOCounters), ('ProcessMemoryLimit', ctypes.c_size_t),
            ('JobMemoryLimit', ctypes.c_size_t), ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
    result, returned = ExtendedLimits(), wintypes.DWORD()
    need(api.QueryInformationJobObject(handle, 9, ctypes.byref(result), ctypes.sizeof(result), ctypes.byref(returned)) and
         returned.value == ctypes.sizeof(result), 'Actual worker owning Job limits readback')
    need(result.BasicLimitInformation.LimitFlags == WindowsJob.FLAGS and result.BasicLimitInformation.ActiveProcessLimit == 1 and
         result.BasicLimitInformation.PerProcessUserTimeLimit == WindowsJob.CPU_100NS and result.ProcessMemoryLimit == WindowsJob.MEMORY_BYTES,
         'Actual worker kill/CPU/memory/single-process limits before public observation')


def worker(root, output, job_handle):
    # No network/API/tool can be reached before the parent's exact assignment GO.
    need(sys.stdin.buffer.readline(16) == b'GO742\n', 'Owned Job assignment GO missing')
    need(os.name == 'nt', 'Real acquisition is Windows-only and must be Job-contained')
    verify_worker_job(job_handle)
    started = time.monotonic()
    deadline = started + ACQUISITION_SECONDS
    plan, _identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=deadline)
    pins = {output: directory_pin(output), output / 'public': directory_pin(output / 'public'),
            output / 'private': directory_pin(output / 'private')}
    budget = NetworkBudget(deadline)
    results = []
    for index, row in enumerate(plan['requests']):
        bounded_time(deadline, 'Acquisition allocation exhausted before remaining fixed requests')
        observed, payload = observe_one(row, plan, budget)
        if payload:
            public = observed.get('public_text_qualified') is True
            name = ('public' if public else 'private') + f'/{index:03d}.' + (row['kind'] if public else 'refused.bin')
            observed['raw_evidence'] = write_exclusive(output, name, payload, pins)
        results.append(observed)
    annotate_checksum_agreement(results)
    after = snapshot_sources(root, plan, deadline=deadline)
    need(before == after, 'Actual source identities changed during observational requests')
    report = {'schema': 'nativecmpkit-Windows-observation-worker742-r1', 'observational_protocol_complete': True,
              'requests_attempted': budget.requests, 'planned_requests': len(plan['requests']),
              'all_payloads_qualified_as_public_text': all(row['public_text_qualified'] for row in results),
              'raw_body_bytes': budget.body_bytes, 'source_inputs_held': True, 'source_inputs_before': before,
              'source_inputs_after': after, 'observations': results, 'no_admission': dict(NO_ADMISSION),
              'archive_reuse': [], 'original14_binaries_or_sidecars_acquired': 0,
              'elapsed_seconds': time.monotonic() - started}
    need(report['elapsed_seconds'] < ACQUISITION_SECONDS and budget.requests == len(plan['requests']),
         'Complete bounded protocol, not an incomplete successful trace')
    write_exclusive(output, 'public/worker-observations.json', json_bytes(report), pins)
    print(json.dumps({'schema': report['schema'], 'observational_protocol_complete': True,
                      'requests_attempted': budget.requests, 'planned_requests': len(plan['requests']),
                      'source_inputs_held': True, 'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0


class WindowsJob:
    """Unnamed owned Job: assignment-before-GO, kill-on-close, one Python process.

    This is process/resource containment, NOT an OS sandbox, ACL assurance,
    general trusted builder or untrusted executable admission.
    """
    FLAGS = 0x00002000 | 0x00000008 | 0x00000100 | 0x00000002
    MEMORY_BYTES = 256 * 1024 * 1024
    CPU_100NS = 60 * 10_000_000

    def __init__(self):
        need(os.name == 'nt', 'Windows Job APIs are mandatory; no Unix fallback')
        from ctypes import wintypes
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        class BasicLimits(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong),
                ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD), ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD)]
        class IOCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                                                              'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]
        class ExtendedLimits(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', IOCounters), ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t), ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
        class Accounting(ctypes.Structure):
            _fields_ = [(name, ctypes.c_longlong) for name in ('TotalUserTime', 'TotalKernelTime', 'ThisPeriodTotalUserTime',
                'ThisPeriodTotalKernelTime')] + [(name, wintypes.DWORD) for name in ('TotalPageFaultCount', 'TotalProcesses',
                'ActiveProcesses', 'TotalTerminatedProcesses')]
        self.Accounting = Accounting
        signatures = {'CreateJobObjectW': ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            'SetInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            'AssignProcessToJobObject': ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            'IsProcessInJob': ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            'QueryInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            'TerminateJobObject': ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            'GetProcessId': ([wintypes.HANDLE], wintypes.DWORD),
            'SetHandleInformation': ([wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD], wintypes.BOOL),
            'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL)}
        for name, (arguments, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self.api.CreateJobObjectW(None, None)
        self.assigned_pid = None
        need(self.handle, 'Create owned unnamed Windows Job refused')
        try:
            limits = ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = self.FLAGS
            limits.BasicLimitInformation.ActiveProcessLimit = 1
            limits.BasicLimitInformation.PerProcessUserTimeLimit = self.CPU_100NS
            limits.ProcessMemoryLimit = self.MEMORY_BYTES
            need(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)),
                 'All kill/active-process/memory/CPU Job limits are mandatory')
        except BaseException:
            self.api.CloseHandle(self.handle)
            self.handle = None
            raise

    def inherit(self, enabled):
        need(self.handle and type(enabled) is bool and self.api.SetHandleInformation(self.handle, 1, 1 if enabled else 0),
             'Exact limited owning Job inheritance preparation/readback')

    def assign(self, process):
        from ctypes import wintypes
        need(self.handle and self.assigned_pid is None and self.api.GetProcessId(process._handle) == process.pid,
             'Actual stable owned child handle/PID before assignment')
        need(self.api.AssignProcessToJobObject(self.handle, process._handle), 'Owned child Job assignment refused')
        inside = wintypes.BOOL()
        need(self.api.IsProcessInJob(process._handle, self.handle, ctypes.byref(inside)) and inside.value,
             'Actual child Job membership must hold before GO')
        self.assigned_pid = process.pid
        need(self.active_processes() == 1, 'Exactly one assigned Python child before GO')

    def active_processes(self):
        from ctypes import wintypes
        need(self.handle, 'Fresh owned Job handle required')
        result, returned = self.Accounting(), wintypes.DWORD()
        need(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(result), ctypes.sizeof(result), ctypes.byref(returned)) and
             returned.value == ctypes.sizeof(result), 'Actual owned Job accounting readback refused')
        return result.ActiveProcesses

    def terminate(self):
        need(self.handle and self.api.TerminateJobObject(self.handle, 742), 'Owned Job termination refused')

    def close(self):
        need(self.handle and self.api.CloseHandle(self.handle), 'Owned Job handle close refused')
        self.handle = None


def assigned_go(process, job):
    job.assign(process)
    need(job.assigned_pid == process.pid and job.active_processes() == 1, 'Actual single child Job before GO')
    process.stdin.write(b'GO742\n')
    process.stdin.flush()
    process.stdin.close()


def safe_environment(runtime, executable, original):
    systemroot = original.get('SYSTEMROOT') or original.get('SystemRoot')
    need(type(systemroot) is str and Path(systemroot).is_absolute() and Path(systemroot).is_dir(), 'Actual Windows system root')
    home, tmp = str(runtime / 'home'), str(runtime / 'tmp')
    # No PATH/JAVA/RUST/GRADLE/Python, proxy/auth/cookie/certificate override or
    # action token values are inherited. Python -I -S -B additionally isolates.
    return {'SYSTEMROOT': systemroot, 'WINDIR': systemroot,
            'PATH': str(executable.parent) + os.pathsep + str(Path(systemroot) / 'System32'),
            'HOME': home, 'USERPROFILE': home, 'TMP': tmp, 'TEMP': tmp, 'LANG': 'C', 'LC_ALL': 'C'}


def manual_context(environment):
    values = {key: environment.get(key) for key in ('GITHUB_REPOSITORY', 'GITHUB_EVENT_NAME', 'GITHUB_REF',
             'NATIVECMPKIT_OBSERVATION_PLATFORM', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')}
    need(values['GITHUB_REPOSITORY'] == REPOSITORY and values['GITHUB_EVENT_NAME'] == 'workflow_dispatch' and
         values['GITHUB_REF'] == REF and values['NATIVECMPKIT_OBSERVATION_PLATFORM'] == CHOICE and
         type(values['GITHUB_SHA']) is str and re.fullmatch('[0-9a-f]{40}', values['GITHUB_SHA']) and
         all(type(values[key]) is str and re.fullmatch('[1-9][0-9]{0,19}', values[key])
             for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')), 'Exact isolated manual observation context')
    need(os.name == 'nt' and sys.version_info[:2] == (3, 12), 'Actual Windows/Python3.12 observational host')
    return values


def controller(root):
    started = time.monotonic()
    deadline, execution_deadline = started + TOTAL_SECONDS, started + TOTAL_SECONDS - CLEANUP_SECONDS
    context = manual_context(os.environ)
    plan, plan_identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=execution_deadline)
    output = root.joinpath(*relative_path(OUTPUT).parts)
    # Existing complete/failed outputs never admit replay. Only bounded owning
    # build parents may be newly created; they are retained, not broadly removed.
    pins = {root: directory_pin(root)}
    current = root
    for part in output.relative_to(root).parts:
        next_path = current / part
        if next_path == output or not next_path.exists():
            create_owned(next_path, pins)
        else:
            pins[next_path] = directory_pin(next_path)
        current = next_path
    for name in ('public', 'private', 'runtime'):
        create_owned(output / name, pins)
    runtime = output / 'runtime'
    for name in ('home', 'tmp'):
        create_owned(runtime / name, pins)
    write_exclusive(output, 'public/source-intent.json', json_bytes({'schema': 'nativecmpkit-Windows-observation-intent742-r1',
        'context': context, 'plan_identity': plan_identity, 'source_inputs_before': before, 'no_admission': dict(NO_ADMISSION),
        'planned_requests': len(plan['requests']), 'original14_reacquired': 0,
        'process_containment_not_OS_sandbox': True}), pins)
    process = job = None
    primary = None
    child_exit = None
    after = None
    cleanup = []
    threads = []
    capture_overflow = threading.Event()
    capture_errors = []
    captured = [0]
    capture_lock = threading.Lock()
    def capture(stream, relative):
        try:
            log = bytearray()
            while True:
                block = stream.read(65536)
                if not block:
                    break
                with capture_lock:
                    room = MAX_CAPTURE - captured[0]
                    portion = block[:max(0, room)]
                    log.extend(portion)
                    captured[0] += len(portion)
                    if len(portion) != len(block):
                        capture_overflow.set()
                        break
            write_exclusive(output, relative, bytes(log), pins)
        except BaseException as error:
            capture_errors.append({'stream': relative, 'exception_type': type(error).__name__})
        finally:
            stream.close()
    try:
        job = WindowsJob()
        executable = Path(sys.executable).resolve(strict=True)
        argv = [str(executable), '-I', '-S', '-B', '-u', str(Path(__file__).resolve()), '--worker', '--job-handle', str(int(job.handle))]
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {'handle_list': [int(job.handle)]}
        job.inherit(True)
        try:
            process = subprocess.Popen(argv, cwd=runtime, env=safe_environment(runtime, executable, os.environ),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True, startupinfo=startup)
        finally:
            job.inherit(False)
        for stream, relative in ((process.stdout, 'private/worker.stdout'), (process.stderr, 'private/worker.stderr')):
            thread = threading.Thread(target=capture, args=(stream, relative), daemon=False)
            thread.start()
            threads.append(thread)
        assigned_go(process, job)
        while process.poll() is None:
            bounded_time(execution_deadline, 'Owned observational child exceeded shared570s allocation')
            need(not capture_overflow.is_set() and not capture_errors, 'Bounded owned child streams refused')
            need(job.active_processes() <= 1, 'No descendant process or alternate tooling allowed')
            time.sleep(0.05)
        child_exit = process.wait(timeout=min(1, bounded_time(execution_deadline, 'Direct child terminal budget')))
        need(child_exit == 0, 'Original observational worker result was not complete')
    except BaseException as error:
        primary = {'exception_type': type(error).__name__}
    finally:
        if process is not None:
            try:
                if job is not None and job.assigned_pid == process.pid:
                    job.terminate()
                    cleanup.append({'owned_job_terminated': True})
                elif process.poll() is None:
                    # Still blocked before GO; terminate only this direct owned
                    # stable Popen handle, never a guessed PID/foreign process.
                    process.terminate()
                    cleanup.append({'unassigned_direct_child_terminated': True, 'GO_sent': False})
                child_exit = process.wait(timeout=min(CLEANUP_SECONDS, bounded_time(deadline, 'Owned child cleanup reserve')))
                cleanup.append({'direct_child_terminal': True, 'exit': child_exit})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'direct_child_terminal': False})
        job_empty = False
        if job is not None:
            try:
                while job.active_processes():
                    bounded_time(deadline, 'Owned Job empty accounting cleanup reserve')
                    time.sleep(0.02)
                job_empty = True
                cleanup.append({'owned_job_active_processes': 0})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_job_empty': False})
            try:
                job.close()  # KILL_ON_JOB_CLOSE holds even an earlier refusal.
                cleanup.append({'owned_job_handle_closed': True})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_job_handle_closed': False})
        for thread in threads:
            try:
                thread.join(timeout=bounded_time(deadline, 'Bounded capture-thread cleanup reserve'))
                need(not thread.is_alive(), 'Owned capture thread remains')
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'capture_thread_terminal': False})
        try:
            after = snapshot_sources(root, plan, deadline=deadline)
            need(before == after, 'Actual source before/after custody differs')
        except BaseException as error:
            cleanup.append({'exception_type': type(error).__name__, 'source_inputs_held': False})
        direct_terminal = process is not None and process.poll() is not None
        for path in (runtime / 'home', runtime / 'tmp', runtime):
            try:
                bounded_time(deadline, 'Owned empty runtime cleanup allocation')
                need(job_empty and direct_terminal and not any(thread.is_alive() for thread in threads),
                     'Fresh Job-empty/direct-terminal/thread-terminal precede owned runtime cleanup')
                need(directory_pin(path.parent) == pins[path.parent] and directory_pin(path) == pins[path],
                     'Fresh owning parent/child directory pins before empty removal')
                path.rmdir()  # Empty only: unexpected worker files are retained/refused, not recursively deleted.
                cleanup.append({'owned_empty_directory_removed': path.name})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_empty_directory_removed': False})
    worker_report = None
    report_error = None
    try:
        worker_payload, worker_identity = read_regular(output, 'public/worker-observations.json', MAX_BODY + SOURCE_LIMIT)
        worker_report = strict_json(worker_payload)
        need(worker_report.get('schema') == 'nativecmpkit-Windows-observation-worker742-r1' and
             worker_report.get('observational_protocol_complete') is True and worker_report.get('no_admission') == NO_ADMISSION and
             worker_report.get('requests_attempted') == worker_report.get('planned_requests') == len(plan['requests']) and
             worker_report.get('source_inputs_before') == worker_report.get('source_inputs_after') == before and
             worker_report.get('original14_binaries_or_sidecars_acquired') == 0,
             'Exact complete untrusted worker receipt; never dependency/native admission')
    except BaseException as error:
        report_error = {'exception_type': type(error).__name__}
    elapsed = time.monotonic() - started
    complete = (primary is None and report_error is None and child_exit == 0 and before == after and
                job_empty and direct_terminal and not capture_overflow.is_set() and not capture_errors and
                not any(thread.is_alive() for thread in threads) and elapsed < TOTAL_SECONDS and
                not any('exception_type' in row for row in cleanup) and worker_report is not None)
    report = {'schema': 'nativecmpkit-Windows-observation-controller742-r1',
        'observational_protocol_complete': complete, 'child_exit': child_exit, 'context': context,
        'primary_refusal': primary, 'worker_receipt_refusal': report_error, 'source_inputs_held': before == after,
        'elapsed_seconds': elapsed, 'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
        'combined_captured_bytes': captured[0], 'capture_overflow': capture_overflow.is_set(), 'capture_errors': capture_errors,
        'owned_job_empty': job_empty, 'owned_direct_child_terminal': direct_terminal, 'cleanup': cleanup,
        'no_admission': dict(NO_ADMISSION), 'original14_or_sidecars_reacquired': 0,
        'Gradle_wrapper_Java_Rust_JAR_ZIP_native_policy_execution': 0, 'OS_sandbox_or_trusted_builder_claim': False}
    write_exclusive(output, 'public/controller-result.json', json_bytes(report), pins)
    terminal_elapsed = time.monotonic() - started
    if terminal_elapsed >= TOTAL_SECONDS:
        write_exclusive(output, 'public/terminal-budget-refusal.json', json_bytes({'schema': report['schema'],
            'observational_protocol_complete': False, 'elapsed_seconds': terminal_elapsed, 'no_admission': dict(NO_ADMISSION)}), pins)
        return 2
    print(json.dumps({'schema': report['schema'], 'observational_protocol_complete': complete,
                      'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--job-handle', type=int)
    args = parser.parse_args()
    if args.worker:
        need(args.job_handle is not None, 'A contained worker requires the owning inherited Job handle')
        return worker(ROOT, ROOT.joinpath(*relative_path(OUTPUT).parts), args.job_handle)
    need(args.job_handle is None, 'Job handle is internal; no caller-controlled controller options')
    return controller(ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
