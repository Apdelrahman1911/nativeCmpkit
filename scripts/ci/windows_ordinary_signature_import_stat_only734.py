# SPDX-License-Identifier: Apache-2.0
"""Fixed-path stat-only failed-import diagnostic, NOT an observation or repair.

No base-source body read/hash/exec, observer import, controller, worker, GET,
signature/key/payload, caller options or environment selection is performed.
An equal fresh pair only ends this diagnostic; it does not admit a retry.
"""
import json
import os
from pathlib import Path
import stat
import sys

BASE_PATH = 'scripts/ci/windows_ordinary_dependency_observer742.py'
BASE_BYTES = 65242


def _fixed_import_stat_only(ROOT):
    # Same pre-read fixed-source lstat/fstat sequence; stop here on BOTH outcomes.
    path = ROOT / BASE_PATH
    if ROOT.resolve(strict=True) != ROOT or path.resolve(strict=True) != path:
        raise ValueError('Exact owning root/base source only, no import alias')
    source_fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    def view(info):
        return tuple(getattr(info, key) for key in source_fields)
    def directory_view(info):
        return (info.st_dev, info.st_ino, info.st_mode, getattr(info, 'st_file_attributes', 0))
    parents = []
    for parent in (ROOT, ROOT / 'scripts', ROOT / 'scripts/ci'):
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('Import source directory reparse/link refused')
        parents.append((parent, directory_view(info)))
    before = path.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != BASE_BYTES or
            getattr(before, 'st_file_attributes', 0) & 1024):
        raise ValueError('Exact bounded unshared legacy source only')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NOATIME', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        named_values, descriptor_values = view(before), view(opened)
        if not all(type(value) is int and len(str(value)) <= 64
                   for value in named_values + descriptor_values):
            raise ValueError('Named/descriptor import source differs')
        detail = json.dumps({'fields': list(source_fields),
            'named7_decimal': [str(value) for value in named_values],
            'descriptor7_decimal': [str(value) for value in descriptor_values],
            'differing_zero_based_indexes': [index for index, (named_value, descriptor_value)
                in enumerate(zip(named_values, descriptor_values)) if named_value != descriptor_value]},
            sort_keys=True, separators=(',', ':'))
        if len(detail) > 2048:
            raise ValueError('Named/descriptor import source differs')
        if view(opened) != view(before):
            raise ValueError('Named/descriptor import source differs; numeric-only=' + detail)
        return detail
    finally:
        os.close(fd)


def main():
    try:
        if len(sys.argv) != 1 or os.name != 'nt' or sys.version_info[:2] != (3, 12):
            raise ValueError('Fixed Windows3.12 stat-only entry, no caller options')
        root = Path(__file__).resolve(strict=True).parents[2]
        detail = _fixed_import_stat_only(root)
    except BaseException as error:
        prefix = 'Named/descriptor import source differs; numeric-only='
        text = str(error)
        if type(error) is not ValueError or not text.startswith(prefix) or len(text) > len(prefix) + 2048:
            text = 'Fixed import stat-only refused; numeric operands unavailable: ' + type(error).__name__
        sys.stderr.write(text + '\n')
        return 1
    print(detail, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
