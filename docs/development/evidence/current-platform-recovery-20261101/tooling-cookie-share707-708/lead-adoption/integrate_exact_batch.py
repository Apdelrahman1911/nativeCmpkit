"""Lead-only exact source adoption; no tests, dispatch, issue or publishing work.

Existing modes come from actual ROOT custody, never private donor modes. New
files get explicit 0644 even under umask 077. Refusals retain a per-file journal;
the script never retries a partial write or rolls unrelated source back.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
HEAD = '2ee751a203f488249839873bfe6590edd73b65ea'
TREE = '13c1e99a619170990d34280c7c75bc3f1fc3f356'
BRANCH = 'development/preview-hardening'
MAX_BYTES = 4 * 1024**2
FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_record(name, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    fd = os.open(OUT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def safe(base, relative):
    need(type(relative) is str and relative and not relative.startswith('/')
         and '\\' not in relative and all(p not in ('', '.', '..') for p in relative.split('/')),
         'Noncanonical source path')
    path = base
    for p in relative.split('/'):
        path /= p
        need(not path.is_symlink(), 'Symlinked source ancestry')
    return path


def read(path):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_BYTES,
         'Bounded ordinary unshared source required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        need(tuple(getattr(os.fstat(stream.fileno()), f) for f in FIELDS)
             == tuple(getattr(before, f) for f in FIELDS), 'Input displaced before read')
        raw = stream.read(MAX_BYTES + 1)
    after = path.lstat()
    need(tuple(getattr(before, f) for f in FIELDS) == tuple(getattr(after, f) for f in FIELDS)
         and len(raw) == before.st_size, 'Input changed during read')
    return raw, {'sha256': digest(raw), 'bytes': len(raw), 'mode': stat.S_IMODE(before.st_mode),
                 'identity': [getattr(before, f) for f in FIELDS]}


def git(*arguments):
    result = subprocess.run(['git', *arguments], cwd=ROOT, check=True, capture_output=True, timeout=60)
    need(len(result.stdout) <= 8 * 1024**2 and len(result.stderr) <= 1024**2, 'Unbounded Git output')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', required=True, type=Path)
    parser.add_argument('--recipe-sha256', required=True)
    parser.add_argument('--review', required=True, type=Path)
    parser.add_argument('--review-sha256', required=True)
    args = parser.parse_args()
    recipe_raw, recipe_custody = read(args.recipe)
    review_raw, review_custody = read(args.review)
    need(digest(recipe_raw) == args.recipe_sha256 and digest(review_raw) == args.review_sha256,
         'Exact final recipe and independent review required')
    recipe, review = json.loads(recipe_raw), json.loads(review_raw)
    need(type(recipe) is dict and type(review) is dict and recipe['source_adopted'] is False,
         'Only unadopted final source packet permitted')
    need(recipe['lead_frozen_head'] == HEAD and recipe['lead_frozen_tree'] == TREE,
         'Recipe authority differs')
    need(git('rev-parse', 'HEAD').decode().strip() == HEAD
         and git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
         and git('branch', '--show-current').decode().strip() == BRANCH
         and not git('status', '--porcelain=v1', '--untracked-files=all').strip(),
         'Clean immutable authorized development ROOT required')
    candidate = Path(recipe['candidate_root']).resolve(strict=True)
    need(candidate.is_relative_to(OUT.parent) and not candidate.is_relative_to(ROOT), 'External candidate required')
    existing, added = recipe['existing17'], recipe['added38']
    held = recipe['held225_frozen_metadata_match']
    inputs = recipe['current280_inputs']
    need(len(existing) == 17 and len(added) == 38 and len(held) == 225 and len(inputs) == 280,
         'Exact 17/38/225 source union required')
    paths = [r['path'] for r in existing + added]
    need(len(set(paths)) == 55 and not (set(paths) & set(held)) and set(paths) | set(held) == set(inputs),
         'Source populations overlap or omit inputs')
    postimages, before, candidate_inputs, held_inputs = {}, {}, {}, {}
    for relative, expected in inputs.items():
        raw, observation = read(safe(candidate, relative))
        need(observation['sha256'] == expected['sha256'] and observation['bytes'] == expected['bytes']
             and observation['mode'] == expected['mode'], 'Frozen candidate input differs: ' + relative)
        candidate_inputs[relative] = observation
        if relative in paths:
            postimages[relative] = raw
        else:
            original, original_observation = read(safe(ROOT, relative))
            need(original == raw, 'Held ROOT input differs: ' + relative)
            held_inputs[relative] = original_observation
    tracked = {}
    for row in git('ls-tree', '-r', '-z', '--full-tree', HEAD).split(b'\0'):
        if row:
            metadata, relative = row.split(b'\t', 1)
            mode, kind, oid = metadata.decode('ascii').split(' ')
            tracked[relative.decode()] = (mode, kind, oid)
    for row in existing:
        relative = row['path']
        raw, observation = read(safe(ROOT, relative))
        need(observation['sha256'] == row['before_sha256']
             and observation['mode'] == row['actual2ee_beforeimage_mode'] == row['required_ROOT_after_mode']
             and candidate_inputs[relative]['sha256'] == row['after_sha256'],
             'Existing exact preimage/mode differs: ' + relative)
        mode, kind, oid = tracked[relative]
        need(mode == row['frozen2ee_git_mode'] and kind == 'blob'
             and bool(observation['mode'] & 0o111) == (mode == '100755'), 'Existing Git mode differs')
        blob_oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw,
                                usedforsecurity=False).hexdigest()
        need(blob_oid == oid, 'Existing preimage does not match Git blob')
        before[relative] = observation
    for row in added:
        relative = row['path']
        need(relative not in tracked and not safe(ROOT, relative).exists()
             and candidate_inputs[relative]['sha256'] == row['after_sha256'],
             'New path exists or differs: ' + relative)
    need(git('rev-parse', 'HEAD').decode().strip() == HEAD
         and not git('status', '--porcelain=v1', '--untracked-files=all').strip(), 'ROOT changed before write')
    write_record('EXACT-ROOT-PREWRITE.json', {'UTC': datetime.now(timezone.utc).isoformat(),
        'head': HEAD, 'tree': TREE, 'branch': BRANCH, 'recipe': recipe_custody, 'review': review_custody,
        'actual_existing17': before, 'actual_held225': held_inputs, 'candidate280': candidate_inputs,
        'added38_absent': [r['path'] for r in added], 'native_tests_or_Git_mutations': 0})
    journal = []
    try:
        for row in existing + added:
            relative = row['path']
            path = safe(ROOT, relative)
            is_existing = relative in before
            if not is_existing:
                path.parent.mkdir(parents=True, exist_ok=True)
                safe(ROOT, relative)
            flags = os.O_WRONLY | os.O_NOFOLLOW
            flags |= 0 if is_existing else os.O_CREAT | os.O_EXCL
            fd = os.open(path, flags, 0o644)
            entry = {'path': relative, 'state': 'opened', 'existing': is_existing}
            journal.append(entry)
            with os.fdopen(fd, 'wb') as stream:
                opened = os.fstat(stream.fileno())
                if is_existing:
                    need([getattr(opened, f) for f in FIELDS] == before[relative]['identity'],
                         'Existing preimage displaced at write boundary')
                    stream.truncate(0)
                else:
                    need(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and opened.st_size == 0,
                         'New destination not exclusive ordinary empty file')
                    os.fchmod(stream.fileno(), 0o644)
                stream.write(postimages[relative])
                stream.flush()
                os.fsync(stream.fileno())
            raw, observation = read(path)
            target_mode = row['required_ROOT_after_mode'] if is_existing else 0o644
            need(raw == postimages[relative] and observation['mode'] == target_mode,
                 'Written source or ROOT mode differs')
            entry.update(state='verified', after=observation)
        after = {}
        for relative, expected in inputs.items():
            raw, observation = read(safe(ROOT, relative))
            need(observation['sha256'] == expected['sha256'] and observation['bytes'] == expected['bytes'],
                 'ROOT final exact source endpoint differs')
            if relative in held_inputs:
                need(observation == held_inputs[relative], 'Held ROOT input displaced during source adoption')
            after[relative] = observation
        changed = git('status', '--porcelain=v1', '--untracked-files=all').decode().splitlines()
        need({line[3:] for line in changed} == set(paths) and len(changed) == 55
             and git('rev-parse', 'HEAD').decode().strip() == HEAD, 'Unexpected ROOT/Git change')
        write_record('EXACT-ROOT-SOURCE-ADOPTION.json', {'UTC': datetime.now(timezone.utc).isoformat(),
            'source_adopted': True, 'existing17_modes_preserved': True, 'added38_explicit_mode': '0644',
            'held225_unchanged': True, 'after280': after, 'journal': journal,
            'ROOT_source_files_written': 55, 'Git_mutations_dispatches_issue_mutations_publications': 0,
            'tests_compilers_native_consumers_executed': 0, 'release_readiness_certified': False})
        print(json.dumps({'source_adopted': True, 'existing': 17, 'added': 38, 'held': 225,
                          'modes_preserved': True, 'tests_or_Git_mutations': 0}))
    except BaseException as error:
        write_record('EXACT-ROOT-SOURCE-ADOPTION-REFUSAL.json', {
            'UTC': datetime.now(timezone.utc).isoformat(), 'exception_type': type(error).__name__,
            'journal': journal, 'automatic_reapply_or_rollback': False})
        raise


if __name__ == '__main__':
    main()
