#!/usr/bin/env python3
"""Bounded, read-only candidate inspection; never emit matched values.

Preparation/self-test does not enumerate the candidate. --scan requires a lead
freeze label. The sole repository write is a NEW additive evidence directory,
created after the final read-only stability check. It is explicitly excluded
from that observation rather than claimed to self-verify.
"""
import argparse
import ast
import collections
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import sys
import tarfile
import zipfile
import zlib

LIMITS = {
    "candidate_entries": 10000,
    "file_bytes": 16 * 1024 * 1024,
    "candidate_regular_bytes": 256 * 1024 * 1024,
    "archive_members_each": 512,
    "archive_member_bytes": 8 * 1024 * 1024,
    "archive_expanded_bytes_each": 16 * 1024 * 1024,
    "archive_expanded_bytes_total": 64 * 1024 * 1024,
    "archive_compression_ratio": 200,
    "archive_depth": 1,
    "matches_per_payload": 10000,
    "status_bytes": 8 * 1024 * 1024,
}
PATTERNS = {
    "private-key-header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token-shaped": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "github-fine-grained-token-shaped": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "aws-access-key-shaped": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "google-api-key-shaped": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "npm-token-shaped": re.compile(rb"\bnpm_[A-Za-z0-9]{30,}\b"),
    "aws-session-key-shaped": re.compile(rb"\bASIA[0-9A-Z]{16}\b"),
    "slack-token-shaped": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,200}\b"),
    "stripe-live-secret-shaped": re.compile(rb"\bsk_live_[A-Za-z0-9]{16,200}\b"),
    "credential-bearing-url": re.compile(rb"(?i)\b(?:https?|ftp|socks5?|ssh|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s/@:?#]{1,256}:[^\s/@?#]{1,256}@"),
    "authorization-literal": re.compile(rb"(?i)\bauthorization\b[\"']?\s*[:=]\s*[\"']?(?:bearer|basic|token)\s+[A-Za-z0-9+/_=-]{12,1024}"),
    "jwt-shaped": re.compile(rb"\beyJ[A-Za-z0-9_-]{6,4096}\.[A-Za-z0-9_-]{6,4096}\.[A-Za-z0-9_-]{16,4096}\b"),
    "URL-credential-query": re.compile(rb"(?i)[?&](?:access_token|refresh_token|id_token|api_key|apikey|password|passwd|secret|signature|sig|x-amz-signature|x-goog-signature)=[A-Za-z0-9%+/_=.~-]{8,2048}"),
    "credential-named-quoted-literal-needs-context": re.compile(rb"(?i)(?<![A-Za-z0-9_])(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|auth[_-]?token|secret[_-]?key|signing[_-]?key)[\"']?\s*[:=]\s*([\"'])([^\"'\r\n]{8,1024})\1"),
}
PRIVATE_OUTPUT = {
    "environment-assignment-line": re.compile(rb"(?m)^(?:HOME|USER|LOGNAME|PATH|SHELL|JAVA_HOME|ANDROID_HOME|ANDROID_SDK_ROOT|SSH_AUTH_SOCK|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|GITHUB_TOKEN|GH_TOKEN)=[^\r\n]+$"),
    "home-directory-reference": re.compile(rb"(?:/root/|/home/[^/\s<>]{1,100}/|/Users/[^/\s<>]{1,100}/|[A-Za-z]:\\Users\\[^\\\s<>]{1,100}\\)"),
    "android-logcat-line": re.compile(rb"(?m)^\s*(?:[0-9]{4}-)?[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3,6}\s+[0-9]+\s+[0-9]+\s+[VDIWEF]\s+[^\r\n]+"),
    "emulator-console-diagnostic-line": re.compile(rb"(?im)^(?:emulator:\s*(?:INFO|WARNING|ERROR|WARNING)|ERROR\s*\|\s*.*(?:emulat|qemu)|INFO\s*\|\s*Android emulator|.*?qemu-system-[^\s:]+:)"),
    "adb-device-list-line": re.compile(rb"(?m)^List of devices attached\s*$|^(?:emulator-[0-9]{4,6}|[A-Za-z0-9]{12,64})\s+(?:device|offline|unauthorized)(?:\s+.*)?$"),
}
PRIVATE_NAME = re.compile(r"(?i)(?:^|/)(?:\.env(?:\.[^/]*)?|local\.properties|id_(?:rsa|dsa|ecdsa|ed25519)(?:\.pub)?|\.netrc|\.npmrc|\.pypirc|credentials|adbkey(?:\.pub)?|[^/]+\.(?:p12|pfx|jks|keystore|key|pem))$")
RAW_OUTPUT_NAME = re.compile(r"(?i)(?:^|/)(?:[^/]*(?:logcat|bugreport|heapdump|environment-dump|env-dump)[^/]*|[^/]+\.(?:hprof|dmp|core|trace))$")
PLACEHOLDER = re.compile(rb"(?i)(?:REDACTED|PLACEHOLDER|EXAMPLE|DUMMY|NOT[-_ ]?A?[-_ ]?(?:REAL|SECRET|TOKEN)|TEST[-_ ](?:SECRET|TOKEN|KEY)|YOUR[-_ ](?:TOKEN|KEY|SECRET)|\$\{|<[^>]{1,100}>|os\.environ|System\.getenv|providers\.environmentVariable)")


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def safe_path(raw):
    b = os.fsencode(raw)
    for category, regex in PATTERNS.items():
        b = regex.sub(('<REDACTED:' + category + '>').encode(), b)
    return os.fsdecode(b)


def git(root, *args):
    env = dict(os.environ)
    env['GIT_OPTIONAL_LOCKS'] = '0'
    r = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *args], cwd=root,
                       env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError('read-only Git command failed; stderr intentionally not emitted')
    return r.stdout


def parse_status(raw):
    if len(raw) > LIMITS['status_bytes']:
        raise ValueError('status size bound exceeded')
    entries = []
    parts = raw.split(b'\0')
    if parts[-1] != b'':
        raise ValueError('status is not NUL terminated')
    i = 0
    while i < len(parts) - 1:
        item = parts[i]
        i += 1
        if len(item) < 4 or item[2:3] != b' ':
            raise ValueError('malformed porcelain record')
        state = item[:2].decode('ascii')
        name = os.fsdecode(item[3:])
        entry = {'status': state, 'path_raw': name}
        if any(c in state for c in 'RC'):
            if i >= len(parts) - 1:
                raise ValueError('missing rename/copy source')
            entry['source_raw'] = os.fsdecode(parts[i])
            i += 1
        entries.append(entry)
    if len(entries) > LIMITS['candidate_entries']:
        raise ValueError('candidate entry bound exceeded')
    if len({e['path_raw'] for e in entries}) != len(entries):
        raise ValueError('duplicate candidate paths')
    return sorted(entries, key=lambda e: os.fsencode(e['path_raw']))


def snapshot(root):
    head = git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    if not re.fullmatch('[0-9a-f]{40,64}', head):
        raise ValueError('unexpected HEAD')
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip()
    raw = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    return {'head': head, 'branch': safe_path(branch), 'status_sha256': sha(raw),
            'status': parse_status(raw)}, raw


def checked_read(root, rel):
    p = PurePosixPath(rel)
    if p.is_absolute() or not p.parts or any(x in ('', '.', '..') for x in p.parts) or '\\' in rel:
        raise ValueError('unsafe candidate path')
    # Open every path component without following links, not merely the leaf.
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in p.parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = fd
        fd = os.open(p.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError('nonregular candidate; not read')
            if before.st_size > LIMITS['file_bytes']:
                raise ValueError('candidate file size bound exceeded')
            data = bytearray()
            while len(data) <= LIMITS['file_bytes']:
                block = os.read(fd, min(1024 * 1024, LIMITS['file_bytes'] + 1 - len(data)))
                if not block:
                    break
                data.extend(block)
            after = os.fstat(fd)
            fields = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            if any(getattr(before, k) != getattr(after, k) for k in fields):
                raise ValueError('candidate changed while being read')
            if len(data) > LIMITS['file_bytes'] or len(data) != after.st_size:
                raise ValueError('candidate file bound or size mismatch')
            return bytes(data), {'size_bytes': after.st_size, 'mode': oct(stat.S_IMODE(after.st_mode))}
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def text_kind(data):
    if b'\0' in data:
        return 'binary'
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return 'binary'
    if any(c < 9 or 13 < c < 32 for c in data):
        return 'binary'
    return 'utf8-text'


def unsafe_member(name):
    return (not name or name.startswith(('/', '\\')) or '\\' in name
            or bool(re.match(r'^[A-Za-z]:', name)) or '..' in PurePosixPath(name).parts
            or any(ord(c) < 32 or ord(c) == 127 for c in name))


def class_info(data):
    if len(data) < 10 or data[:4] != b'\xca\xfe\xba\xbe':
        raise ValueError('invalid Java class magic/header')
    minor, major, count = struct.unpack_from('>HHH', data, 4)
    if not 45 <= major <= 100 or count == 0:
        raise ValueError('unsupported Java class header')
    pos, idx, utf8_count, utf8_bytes = 10, 1, 0, 0
    constants, classes = {}, {}
    while idx < count:
        if pos >= len(data):
            raise ValueError('truncated Java constant pool')
        tag = data[pos]
        pos += 1
        if tag == 1:
            if pos + 2 > len(data):
                raise ValueError('truncated Java UTF8 length')
            size = struct.unpack_from('>H', data, pos)[0]
            pos += 2
            if pos + size > len(data):
                raise ValueError('truncated Java UTF8 bytes')
            constants[idx] = data[pos:pos+size]
            utf8_count += 1
            utf8_bytes += size
            pos += size
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pos += 4
        elif tag in (5, 6):
            pos += 8
            idx += 1
        elif tag in (7, 8, 16, 19, 20):
            if tag == 7 and pos + 2 <= len(data):
                classes[idx] = struct.unpack_from('>H', data, pos)[0]
            pos += 2
        elif tag == 15:
            pos += 3
        else:
            raise ValueError('unsupported Java constant-pool tag')
        if pos > len(data):
            raise ValueError('truncated Java constant-pool record')
        idx += 1
    if pos + 6 > len(data):
        raise ValueError('truncated Java class identity')
    access, this_class, super_class = struct.unpack_from('>HHH', data, pos)
    name = constants.get(classes.get(this_class))
    if name is None:
        raise ValueError('invalid Java this_class reference')
    return {'magic_valid': True, 'major_version': major, 'minor_version': minor,
            'constant_pool_count': count, 'utf8_constant_count': utf8_count,
            'utf8_constant_bytes': utf8_bytes,
            'class_internal_name': safe_path(name.decode('utf8', 'replace')),
            'constant_pool_end_offset': pos, 'payload_bytes_after_pool': len(data) - pos,
            'method_bytecode_executed': False, 'full_bytecode_verification': False}


class Scan:
    def __init__(self):
        self.matches = []
        self.private_output = []
        self.issues = []
        self.artifacts = []
        self.expanded_total = 0
        self.members = 0
        self.literal_contexts = []

    def issue(self, path, kind, detail=None):
        record = {'path': safe_path(path), 'kind': kind}
        if detail is not None:
            record['detail'] = detail  # Only fixed prose/category metadata; never exception text.
        self.issues.append(record)

    def markers(self, path, data, kind=None):
        kind = kind or text_kind(data)
        found = 0
        for category, regex in PATTERNS.items():
            for m in regex.finditer(data):
                found += 1
                if found > LIMITS['matches_per_payload']:
                    self.issue(path, 'marker-match-bound-exceeded')
                    return
                item = {'path': safe_path(path), 'category': category, 'matched_value': 'REDACTED'}
                if kind == 'utf8-text':
                    item['line'] = data.count(b'\n', 0, m.start()) + 1
                else:
                    item['byte_offset'] = m.start()
                item['explicit_placeholder_indicator'] = bool(PLACEHOLDER.search(m.group()))
                self.matches.append(item)
                if category == 'credential-named-quoted-literal-needs-context':
                    self.literal_contexts.append(self.literal_context(path, data, item))
        if kind == 'utf8-text':
            for category, regex in PRIVATE_OUTPUT.items():
                lines = [data.count(b'\n', 0, m.start()) + 1 for m in regex.finditer(data)]
                if lines:
                    self.private_output.append({'path': safe_path(path), 'category': category,
                                                'count': len(lines), 'lines': lines,
                                                'matched_values': 'REDACTED'})

    def literal_context(self, path, data, item):
        result = {k: item[k] for k in ('path', 'category', 'explicit_placeholder_indicator')}
        line = item.get('line')
        if line:
            result['line'] = line
        result['test_path_shaped'] = bool(re.search(r'(?i)(?:test|fixture|probe)', path))
        result['python_ast_parse_succeeded'] = False
        if path.endswith('.py'):
            try:
                tree = ast.parse(data.decode('utf8'))
                result['python_ast_parse_succeeded'] = True
                nodes = [n for n in ast.walk(tree) if hasattr(n, 'lineno') and n.lineno <= line <= (getattr(n, 'end_lineno', None) or n.lineno)]
                funcs = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                result['inside_test_function'] = any(n.name.startswith('test') for n in funcs)
                result['test_name_indicates_sensitive_material_rejection'] = any(re.search(r'(?i)(?:reject|secret|credential|sensitive)', n.name) for n in funcs)
                result['line_overlaps_ast_string_constant'] = any(isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) for n in nodes)
            except (SyntaxError, UnicodeDecodeError, ValueError, RecursionError):
                pass
        result['disposition'] = 'requires-current-context-review; not automatically a credential or cleared'
        return result

    def member(self, archive, name, data):
        self.members += 1
        self.expanded_total += len(data)
        if self.expanded_total > LIMITS['archive_expanded_bytes_total']:
            self.issue(archive, 'aggregate-archive-expansion-bound-exceeded')
            return {'path': safe_path(name), 'not_scanned': 'aggregate-bound'}
        label = archive + '!' + name
        self.markers(label, data)
        record = {'path': safe_path(name), 'size_bytes': len(data), 'sha256': sha(data), 'kind': text_kind(data)}
        if data[:4] == b'\xca\xfe\xba\xbe' or name.lower().endswith('.class'):
            try:
                record['java_class'] = class_info(data)
            except ValueError:
                self.issue(label, 'malformed-or-unsupported-Java-class')
        if data.startswith((b'PK\x03\x04', b'PK\x05\x06', b'\x1f\x8b')) or name.lower().endswith(('.zip', '.jar', '.tgz', '.tar', '.tar.gz', '.7z', '.xz')):
            record['nested_archive_not_expanded'] = True
            self.issue(label, 'nested-archive-outside-one-layer-scope')
        if name.endswith('package.json') and len(data) <= 1024 * 1024:
            try:
                p = json.loads(data)
                if isinstance(p, dict):
                    scripts = p.get('scripts')
                    record['package_descriptor'] = {
                        'name_is_string': isinstance(p.get('name'), str),
                        'version_is_string': isinstance(p.get('version'), str),
                        'scripts_present': bool(scripts),
                        'script_names': [safe_path(k) for k in scripts] if isinstance(scripts, dict) else [],
                        'dependencies_count': len(p.get('dependencies', {})) if isinstance(p.get('dependencies', {}), dict) else None,
                        'publish_config_present': bool(p.get('publishConfig')),
                    }
            except (ValueError, UnicodeDecodeError):
                self.issue(label, 'package-descriptor-unparseable')
        return record

    def inspect_zip(self, path, data):
        record = {'path': safe_path(path), 'container': 'zip', 'members': [], 'extraction_or_execution': False}
        self.artifacts.append(record)
        try:
            eocd = data.rfind(b'PK\x05\x06', max(0, len(data) - 65557))
            if eocd < 0 or eocd + 22 > len(data):
                raise ValueError('zip-eocd-unavailable')
            disk, startdisk, here, total, cdsize, cdoffset, commentlen = struct.unpack_from('<HHHHIIH', data, eocd + 4)
            if disk or startdisk or here != total or total == 65535 or cdsize == 0xffffffff or cdoffset == 0xffffffff:
                raise ValueError('zip64-or-multidisk-outside-scope')
            if eocd + 22 + commentlen != len(data) or cdoffset + cdsize > eocd:
                raise ValueError('zip-central-directory-layout-unexpected')
            if total > LIMITS['archive_members_each']:
                raise ValueError('archive-member-count-bound-exceeded')
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos = z.infolist()
                if len(infos) != total:
                    raise ValueError('zip-member-count-mismatch')
                record['member_count'] = len(infos)
                record['uncompressed_bytes_declared'] = sum(i.file_size for i in infos)
                if record['uncompressed_bytes_declared'] > LIMITS['archive_expanded_bytes_each']:
                    raise ValueError('archive-expanded-byte-bound-exceeded')
                names = collections.Counter(i.filename for i in infos)
                if any(v > 1 for v in names.values()):
                    self.issue(path, 'duplicate-archive-member-paths')
                for inf in infos:
                    label = path + '!' + inf.filename
                    if unsafe_member(inf.filename):
                        self.issue(label, 'unsafe-archive-member-path-not-read')
                        continue
                    mode = inf.external_attr >> 16
                    if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                        self.issue(label, 'archive-link-or-special-member-not-read')
                        continue
                    if inf.flag_bits & 1:
                        self.issue(label, 'encrypted-archive-member-not-read')
                        continue
                    if inf.is_dir():
                        record['members'].append({'path': safe_path(inf.filename), 'kind': 'directory'})
                        continue
                    if inf.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                        self.issue(label, 'unsupported-zip-compression-not-read')
                        continue
                    if inf.file_size > LIMITS['archive_member_bytes'] or inf.file_size > max(1, inf.compress_size) * LIMITS['archive_compression_ratio']:
                        self.issue(label, 'archive-member-size-or-ratio-bound-exceeded')
                        continue
                    if self.expanded_total + inf.file_size > LIMITS['archive_expanded_bytes_total']:
                        self.issue(label, 'aggregate-archive-expansion-bound-exceeded')
                        continue
                    with z.open(inf) as f:
                        member_data = f.read(LIMITS['archive_member_bytes'] + 1)
                    if len(member_data) != inf.file_size:
                        self.issue(label, 'archive-member-size-mismatch')
                        continue
                    record['members'].append(self.member(path, inf.filename, member_data))
        except ValueError as e:
            self.issue(path, str(e) if str(e) in {'zip-eocd-unavailable', 'zip64-or-multidisk-outside-scope', 'zip-central-directory-layout-unexpected', 'archive-member-count-bound-exceeded', 'zip-member-count-mismatch', 'archive-expanded-byte-bound-exceeded'} else 'zip-value-error')
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, EOFError, zlib.error):
            self.issue(path, 'zip-unreadable-or-unsupported')

    def inspect_tgz(self, path, data):
        record = {'path': safe_path(path), 'container': 'gzip-tar', 'members': [], 'extraction_or_execution': False}
        self.artifacts.append(record)
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as g:
                expanded = g.read(LIMITS['archive_expanded_bytes_each'] + 1)
            if len(expanded) > LIMITS['archive_expanded_bytes_each'] or len(expanded) > max(1, len(data)) * LIMITS['archive_compression_ratio']:
                self.issue(path, 'tgz-expanded-size-or-ratio-bound-exceeded')
                return
            record['tar_bytes_in_memory'] = len(expanded)
            record['gzip_mtime_not_collected'] = True
            count, total, names = 0, 0, set()
            with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as t:
                while True:
                    inf = t.next()
                    if inf is None:
                        break
                    count += 1
                    if count > LIMITS['archive_members_each']:
                        self.issue(path, 'archive-member-count-bound-exceeded')
                        break
                    label = path + '!' + inf.name
                    if inf.name in names:
                        self.issue(label, 'duplicate-archive-member-path')
                    names.add(inf.name)
                    if unsafe_member(inf.name):
                        self.issue(label, 'unsafe-archive-member-path-not-read')
                        continue
                    if inf.isdir():
                        record['members'].append({'path': safe_path(inf.name), 'kind': 'directory'})
                        continue
                    if not inf.isfile():
                        self.issue(label, 'archive-link-or-special-member-not-read')
                        continue
                    total += inf.size
                    if inf.size > LIMITS['archive_member_bytes'] or total > LIMITS['archive_expanded_bytes_each'] or self.expanded_total + inf.size > LIMITS['archive_expanded_bytes_total']:
                        self.issue(label, 'archive-member-or-expansion-bound-exceeded')
                        continue
                    f = t.extractfile(inf)  # Returns an in-memory stream; never extracts to the filesystem.
                    if f is None:
                        self.issue(label, 'archive-regular-member-not-readable')
                        continue
                    with f:
                        member_data = f.read(LIMITS['archive_member_bytes'] + 1)
                    if len(member_data) != inf.size:
                        self.issue(label, 'archive-member-size-mismatch')
                        continue
                    rec = self.member(path, inf.name, member_data)
                    rec['executable_mode_bit'] = bool(inf.mode & 0o111)
                    rec['owner_names_present_not_recorded'] = bool(inf.uname or inf.gname)
                    record['members'].append(rec)
            record['member_count'] = count
            record['uncompressed_regular_bytes_declared'] = total
        except (tarfile.TarError, OSError, EOFError, ValueError, zlib.error):
            self.issue(path, 'tgz-unreadable-or-unsupported')

    def payload(self, path, data):
        kind = text_kind(data)
        self.markers(path, data, kind)
        if data.startswith((b'PK\x03\x04', b'PK\x05\x06')) or path.lower().endswith(('.zip', '.jar')):
            self.inspect_zip(path, data)
            return 'zip'
        if data.startswith(b'\x1f\x8b') or path.lower().endswith(('.tgz', '.tar.gz')):
            self.inspect_tgz(path, data)
            return 'gzip-tar'
        if data.startswith(b'\xca\xfe\xba\xbe') or path.lower().endswith('.class'):
            rec = {'path': safe_path(path), 'container': 'java-class', 'extraction_or_execution': False}
            self.artifacts.append(rec)
            try:
                rec.update(class_info(data))
            except ValueError:
                self.issue(path, 'malformed-or-unsupported-Java-class')
            return 'java-class'
        if kind == 'binary':
            self.issue(path, 'opaque-binary-marker-scan-only-needs-manual-review')
        return kind


def verify_original_patterns(root):
    rel = 'scripts/audit/scan_git_secret_markers.py'
    raw, meta = checked_read(root, rel)
    tree = ast.parse(raw.decode())
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'patterns' for t in n.targets))
    categories = []
    for key, value in zip(node.keys, node.values):
        category = ast.literal_eval(key)
        if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute) or value.func.attr != 'compile':
            raise ValueError('unexpected marker definition; historical scanner was not executed')
        regex = ast.literal_eval(value.args[0])
        if PATTERNS[category].pattern != regex:
            raise ValueError('current baseline marker definition differs from prepared scanner')
        categories.append(category)
    return {'path': rel, 'sha256': sha(raw), 'categories': categories, 'loaded_by': 'AST/literal inspection only; historical scanner not executed'}


def run_scan(root, output, freeze):
    root = root.resolve(strict=True)
    if not output.is_absolute():
        output = root / output
    if output.exists():
        raise ValueError('evidence directory must be new')
    parent = output.parent.resolve(strict=True)
    required = root / 'docs/development/evidence/review'
    if parent != required.resolve(strict=True):
        raise ValueError('output must be a direct new child of docs/development/evidence/review')
    if output.name in ('.', '..') or not re.fullmatch('[A-Za-z0-9_.-]+', output.name):
        raise ValueError('invalid evidence directory name')
    scan = Scan()
    started = now()
    pattern_receipt = verify_original_patterns(root)
    before, status_before = snapshot(root)
    entries = []
    path_data = {}
    total = 0
    private_paths, raw_output_paths, log_paths = [], [], []
    staged_content = []
    for e in before['status']:
        rawpath = e['path_raw']
        display = safe_path(rawpath)
        row = {'status': e['status'], 'path': display, 'path_sha256': sha(os.fsencode(rawpath))}
        if 'source_raw' in e:
            row['rename_or_copy_source'] = safe_path(e['source_raw'])
        entries.append(row)
        if display != rawpath:
            scan.issue(display, 'selected-marker-in-candidate-filename')
        if PRIVATE_NAME.search(rawpath):
            private_paths.append(display)
        if RAW_OUTPUT_NAME.search(rawpath):
            raw_output_paths.append(display)
        if rawpath.lower().endswith('.log'):
            log_paths.append(display)
        if 'U' in e['status'] or e['status'] in ('AA', 'DD'):
            scan.issue(rawpath, 'unmerged-candidate-path')
        if e['status'][0] not in (' ', '?'):
            staged_content.append({'path': display, 'status': e['status']})
        try:
            data, meta = checked_read(root, rawpath)
        except FileNotFoundError:
            if 'D' in e['status']:
                row['kind'] = 'deleted-no-new-bytes'
            else:
                row['kind'] = 'not-read'
                scan.issue(rawpath, 'candidate-missing-not-recorded-deleted')
            continue
        except (OSError, ValueError):
            row['kind'] = 'not-read'
            scan.issue(rawpath, 'nonregular-unsafe-unreadable-large-or-changing-path-not-read')
            continue
        total += len(data)
        row.update(meta)
        row['sha256'] = sha(data)
        path_data[rawpath] = row
        if total > LIMITS['candidate_regular_bytes']:
            row['kind'] = 'not-scanned-total-byte-bound'
            scan.issue(rawpath, 'candidate-total-byte-bound-exceeded')
            break
        row['kind'] = scan.payload(rawpath, data)
    # This checkpoint is a WORKTREE candidate review, not an arbitrary staged
    # partial-index review. Fail closed if a partial staged state exists.
    if staged_content:
        scan.issue('(index)', 'staged-index-state-requires-lead-reconciliation',
                   'Worktree bytes were scanned; staged blob contents were not independently scanned. Lead must stage exact reviewed bytes or request separate index verification.')
    middle, status_middle = snapshot(root)
    changed = []
    rechecked = 0
    for rawpath, row in path_data.items():
        try:
            data, meta = checked_read(root, rawpath)
            rechecked += 1
            if sha(data) != row['sha256'] or meta != {k: row[k] for k in ('size_bytes', 'mode')}:
                changed.append(safe_path(rawpath))
        except (OSError, ValueError):
            changed.append(safe_path(rawpath))
    after, status_after = snapshot(root)
    stable_status = status_before == status_middle == status_after
    stable_head = before['head'] == middle['head'] == after['head'] and before['branch'] == middle['branch'] == after['branch']
    if not stable_status:
        scan.issue('(inventory)', 'Git-status-changed-during-scan')
    if not stable_head:
        scan.issue('(repository)', 'HEAD-or-branch-changed-during-scan')
    if changed:
        scan.issue('(worktree)', 'candidate-bytes-or-mode-changed-during-scan')
    ended = now()
    counts = dict(collections.Counter(r.get('kind', 'unknown') for r in entries))
    statuses = dict(collections.Counter(r['status'] for r in entries))
    fingerprints = [{'path': r['path'], 'path_sha256': r['path_sha256'], 'sha256': r['sha256'], 'size_bytes': r['size_bytes'], 'mode': r['mode']} for r in entries if 'sha256' in r]
    report = {
        'schema_version': 1, 'kind': 'fresh-redacted-selected-marker-worktree-candidate-review',
        'started_at_utc': started, 'completed_at_utc': ended, 'lead_freeze_label': freeze,
        'repository': 'Apdelrahman1911/nativeCmpkit',
        'head': before['head'], 'branch': before['branch'],
        'scope': 'Current Git-porcelain tracked changes and nonignored untracked files; whole selected worktree file bytes, not Git history or unchanged tracked files.',
        'inventory_entry_count': len(entries), 'status_counts': statuses, 'file_kind_counts': counts,
        'regular_bytes_read_first_pass': total, 'regular_hashes': len(fingerprints),
        'status_raw_sha256': before['status_sha256'], 'file_manifest_sha256': sha(canonical(fingerprints)),
        'bounds': LIMITS, 'baseline_marker_definition': pattern_receipt,
        'selected_marker_categories': list(PATTERNS), 'private_output_marker_categories': list(PRIVATE_OUTPUT),
        'selected_marker_matches': scan.matches,
        'literal_context_observations': scan.literal_contexts,
        'private_filename_candidates': private_paths,
        'raw_device_or_private_output_filename_candidates': raw_output_paths,
        'log_paths': log_paths, 'private_output_marker_observations': scan.private_output,
        'archive_regular_members_inspected': scan.members, 'archive_regular_member_bytes_inspected': scan.expanded_total,
        'artifacts': scan.artifacts, 'skips_unsupported_or_stability_findings': scan.issues,
        'staged_index_paths_not_independently_scanned': staged_content,
        'stability': {'raw_status_held_at_three_observations': stable_status, 'HEAD_and_branch_held': stable_head,
                      'regular_files_rehashed': rechecked, 'bytes_and_mode_held': not changed,
                      'changed_paths': changed, 'post_status_raw_sha256': after['status_sha256'],
                      'post_head': after['head'], 'post_branch': after['branch']},
        'method': {'enumeration': 'GIT_OPTIONAL_LOCKS=0 git --no-optional-locks -c core.fsmonitor=false status --porcelain=v1 -z --untracked-files=all; NUL parsing including rename/copy source',
                   'reads': 'Component-by-component openat O_NOFOLLOW, regular files only; bounded reads and fstat before/after; no ignored-directory traversal.',
                   'markers': 'Selected raw-byte regexes for every read file/member, including binary ASCII/string constants; text-only private-output markers; matched values/lines never emitted.',
                   'archive_review': 'Bounded BytesIO ZIP and gzip/tar reads; no filesystem extraction, member execution, class loading or network. One archive layer; unsupported/encrypted/link/special/unsafe/bound-exceeding content is explicit.',
                   'java_review': 'Header and constant-pool structural parsing plus selected raw-byte markers; no execution, decompilation or full bytecode verification.',
                   'source_and_library_tests_executed': 0, 'network_calls': 0, 'source_files_modified': 0,
                   'staging_or_commits': 0,
                   'self_exclusion': 'This newly created evidence directory is written ONLY after final snapshot and rehashes. It was absent from, and is not certified by, its own candidate inventory.'},
        'assessment': {'selected_marker_scan_is_secret_clearance': False, 'safe_to_commit_or_publish_certification': False,
                       'manual_context_review_required': True, 'confirmed_secret_findings': None,
                       'issues_closed_or_status_promoted': 0},
        'limitations': [
            'Not exhaustive secret detection, entropy analysis or evidence that unknown/encoded/split/obfuscated/low-entropy credentials do not exist.',
            'Only selected working-tree candidates were read. Unchanged tracked files, deleted old bytes, ignored files, history, remote configuration and files outside the repository are out of scope.',
            'If any staged index state exists, its bytes require separate reconciliation; a later commit must stage the exact reviewed worktree bytes to retain relevance.',
            'Private-output marker absence does not prove all personal identifiers or unrelated terminal content absent. Local-path references and retained build/test logs require context.',
            'Binary raw markers and bounded archive reads do not establish malware absence, runtime correctness, native safety, provenance or license sufficiency.',
            'Java constant-pool review does not validate every bytecode instruction, dependency or full ABI. Intentional fixture artifacts need current source/receipt justification.',
            'Nested archives, links, encryption, unsupported formats and exceeded bounds are reported, never silently counted as scanned.',
            'Rechecking hashes/status narrows races but is not an atomic filesystem snapshot. Any later modification or staging requires a new exact-byte comparison.',
            'The additive review evidence is self-excluded and must be checked separately by the lead. This observation neither lifts containment nor authorizes publication.'
        ],
    }
    # No file has been written inside the repository before this point.
    output.mkdir(mode=0o755)
    (output / 'scan.json').write_bytes(json_bytes(report))
    (output / 'candidate-files.json').write_bytes(json_bytes(entries))
    (output / 'candidate-file-fingerprint.json').write_bytes(json_bytes(fingerprints))
    (output / 'scanner.py').write_bytes(Path(__file__).read_bytes())
    checksum_files = sorted(p for p in output.iterdir() if p.is_file())
    (output / 'SHA256SUMS').write_text(''.join(sha(p.read_bytes()) + '  ' + p.name + '\n' for p in checksum_files))
    summary = {k: report[k] for k in ('inventory_entry_count', 'status_counts', 'file_kind_counts', 'regular_bytes_read_first_pass', 'archive_regular_members_inspected')}
    summary.update({'evidence': str(output.relative_to(root)), 'selected_marker_match_count': len(scan.matches),
                    'private_filename_candidate_count': len(private_paths), 'private_output_observation_groups': len(scan.private_output),
                    'skips_or_stability_findings': len(scan.issues), 'stable': stable_status and stable_head and not changed,
                    'manual_context_review_pending': True})
    print(json.dumps(summary, indent=2))
    return 0 if not scan.issues and summary['stable'] else 2


def self_test():
    # Pure synthetic in-memory checks; no worktree status/inventory/read/build.
    entries = parse_status(b' M one\0?? two words\0R  dest\0source\0 D deleted\0')
    assert len(entries) == 4
    assert next(e for e in entries if e['path_raw'] == 'dest')['source_raw'] == 'source'
    assert unsafe_member('../escape') and unsafe_member('/absolute') and unsafe_member('C:/x') and unsafe_member('a\\b')
    assert not unsafe_member('package/package.json')
    scan = Scan()
    scan.markers('synthetic.txt', b'credential=' + b'ghp_' + b'Q' * 30 + b'\n')
    assert len(scan.matches) == 1 and scan.matches[0]['matched_value'] == 'REDACTED'
    assert b'Q' * 30 not in canonical(scan.matches)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('licenses/LICENSE.txt', b'Inert synthetic text.\n')
    scan2 = Scan()
    scan2.inspect_zip('synthetic.zip', buf.getvalue())
    assert not scan2.issues and scan2.members == 1
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as t:
        payload = b'{"name":"synthetic-fixture","version":"0.0.0"}\n'
        member = tarfile.TarInfo('package/package.json')
        member.size = len(payload)
        t.addfile(member, io.BytesIO(payload))
    scan3 = Scan()
    scan3.inspect_tgz('synthetic.tgz', gzip.compress(buf.getvalue(), mtime=0))
    assert not scan3.issues and scan3.members == 1
    assert not scan3.artifacts[0]['members'][0]['package_descriptor']['scripts_present']
    evil = io.BytesIO()
    with zipfile.ZipFile(evil, 'w') as z:
        z.writestr('../escape', b'inert')
    scan4 = Scan()
    scan4.inspect_zip('synthetic-bad.zip', evil.getvalue())
    assert scan4.issues and scan4.members == 0
    # Minimal structural class fixture; never loaded or run.
    name = b'local/Synthetic'
    klass = b'\xca\xfe\xba\xbe' + struct.pack('>HHH', 0, 61, 3) + b'\x01' + struct.pack('>H', len(name)) + name + b'\x07\x00\x01' + struct.pack('>HHH', 0x21, 2, 0)
    assert class_info(klass)['major_version'] == 61
    print(json.dumps({'helper_self_test': 'passed', 'candidate_scan_run': False,
                      'checks': ['porcelain-NUL-renames', 'unsafe-member-paths', 'redacted-marker-output', 'bounded-ZIP-read', 'bounded-TGZ-read', 'unsafe-ZIP-member-rejected', 'Java-constant-pool-parse'],
                      'bounds': LIMITS}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--scan', action='store_true')
    p.add_argument('--root', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--freeze-label')
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not all((args.root, args.output, args.freeze_label)):
        p.error('--scan requires --root, --output and lead-authorized --freeze-label')
    return run_scan(args.root, args.output, args.freeze_label)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, StopIteration) as exc:
        # No arbitrary exception message/path/terminal content escapes redaction.
        print(json.dumps({'error': 'bounded scan failed before completion; inspect helper privately',
                          'exception_type': type(exc).__name__, 'matched_values_emitted': False}))
        raise SystemExit(3)
