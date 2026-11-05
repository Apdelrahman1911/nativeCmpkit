# CONTEXT STAT-ONLY: quoted original prologue/constants below are passive, NOT acquisition authority.
# The only runtime operation is the pre-read fixed-base stat comparison, then owned close and exit.
# SPDX-License-Identifier: Apache-2.0
"""One NEW source-held Central detached-signature acquisition, NOT admission.

Cached authenticated source303 metadata is fixed in reviewed source, not read
from an arbitrary caller archive/file and never reGETted. At most one target is
requested; every redirect refuses without a hop or fallback. Any captured body
is PRIVATE and UNINSPECTED. No signature syntax/key/crypto or cached POM access
is granted. This is Windows runner prerequisite work, not NATIVE-005 tests.
The immutable legacy Win32/owned Job/GO/descriptor/cleanup primitives are reused
unchanged; no host, base constant or function overrides.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import stat
import subprocess
import sys
import threading
import time
import types
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = 'scripts/ci/windows_ordinary_dependency_observer742.py'
BASE_SHA256 = '23c89b500571dff6f347a349b59391e0b6c816493f08b2232130f7aa73d82c14'
BASE_BYTES = 65242
OWN_PATH = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
PLAN = 'scripts/ci/windows-ordinary-signature734-plan.json'
PLAN_SHA256 = 'bf3cdca3083092e7e79ab583e34d48eb04a8e7bd1d337963e1a1aad5bf266632'
CACHE_PATH = 'scripts/ci/windows-ordinary-signature734-source303.json'
CACHE_SHA256 = '58fcf624993d8663fd87602124c94bc652ee2aba1f56a51eb86f41a314ff64cd'
CACHE_BYTES = 2813
OUTPUT = 'build/ci-verification/windows-ordinary-signature734'
CHOICE = 'windows-ordinary-dependency-observation1'
REPOSITORY = 'Apdelrahman1911/nativeCmpkit'
REF = 'refs/heads/development/javafx-ordinary-consumer1'
TOTAL_SECONDS = 90
CLEANUP_SECONDS = 15
ACQUISITION_SECONDS = 60
IO_SECONDS = 20
MAX_REQUESTS = 1
MAX_BODY = 524288
MAX_TOTAL_BODY = 524288
MAX_CAPTURE = 65536
SOURCE_LIMIT = 1048576
MAX_HEADERS = 64
MAX_HEADER_BYTES = 16384
MAX_PUBLIC_LOCATION = 2048
PLAN_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-plan734-r2'
WORKER_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-worker734-r2'
INTENT_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-intent734-r2'
CONTROLLER_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-controller734-r2'
CACHE_SCHEMA = 'nativecmpkit-Windows-signature-source303-metadata734-r2'
CACHE_KEYS = frozenset(['Location_sha256', 'NO_ADMISSION', 'REVIEWED_EXPECTATIONS_SHA256', 'basis', 'metadata_is_not_routing_or_publisher_authority', 'requires_new_lead_source_result_review_before_dispatch', 'schema', 'source_record', 'source_record_index'])
CACHED_ROW_KEYS = frozenset(['Location_header_count', 'automatic_redirects_followed', 'body_bytes', 'body_sha256', 'canonical_publisher_target_authenticated', 'close_errors', 'complete_response', 'credential_cookie_proxy_inheritance', 'evidence_role', 'exception_type', 'headers_complete', 'http_status', 'id', 'independent_trust_or_consumer_acceptance', 'kind', 'network_request_started', 'original_GET_headers_reconstructed', 'other_redirects_refused', 'public_Location', 'public_Location_is_not_routing_or_publisher_authority', 'public_text_qualified', 'publisher_provenance_qualified', 'seed', 'signature_cryptographically_verified', 'status', 'unqualified_Location_sha256', 'url'])
BASIS_SHA256 = '4fecb8049990487da1df725eac45248af638e10ffe8b45ac592ed18e93e68870'
CACHED_ROW_SHA256 = '5765ca9a3fdf6466c3bbd7b0cb48ef73c63c0a3c4ebe9cd7b20eeefc61d73ee4'
EXACT_LIMITS = {'total_seconds': 90, 'acquisition_seconds': 60, 'cleanup_seconds': 15, 'io_seconds': 20, 'max_requests': 1, 'max_body_bytes': 524288, 'max_total_body_bytes': 524288, 'max_capture_bytes': 65536}
EXACT_TARGET = {'id': 'routed-convention-vanniktech-maven-publish-central:pom.asc', 'seed': 'routed-convention-vanniktech-maven-publish-central', 'kind': 'pom.asc', 'url': 'https://repo.maven.apache.org/maven2/com/vanniktech/maven/publish/com.vanniktech.maven.publish.gradle.plugin/0.37.0/com.vanniktech.maven.publish.gradle.plugin-0.37.0.pom.asc'}
EXACT_SEED = {'id': 'routed-convention-vanniktech-maven-publish-central', 'repository': 'central', 'group': 'com.vanniktech.maven.publish', 'module': 'com.vanniktech.maven.publish.gradle.plugin', 'version': '0.37.0'}
EXACT_SOURCE_ID = 'convention-vanniktech-maven-publish:pom.asc'
EXACT_SOURCE_SEED = 'convention-vanniktech-maven-publish'
EXACT_SOURCE_URL = 'https://plugins.gradle.org/m2/com/vanniktech/maven/publish/com.vanniktech.maven.publish.gradle.plugin/0.37.0/com.vanniktech.maven.publish.gradle.plugin-0.37.0.pom.asc'
EXACT_SOURCE_COORDINATE = {'id': 'convention-vanniktech-maven-publish', 'repository': 'plugin-portal', 'group': 'com.vanniktech.maven.publish', 'module': 'com.vanniktech.maven.publish.gradle.plugin', 'version': '0.37.0'}
EXACT_LOCATION_SHA256 = '6d0184b9d70fe09728b848dd4f211681b7efc6c888856107f58729a96489e47b'
SOURCE_FALSE_FIELDS = ('automatic_redirects_followed', 'canonical_publisher_target_authenticated', 'credential_cookie_proxy_inheritance', 'independent_trust_or_consumer_acceptance', 'original_GET_headers_reconstructed', 'public_text_qualified', 'publisher_provenance_qualified', 'signature_cryptographically_verified')
OLD_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_dependency_cause_observer734.py\n'
NEW_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_vanniktech_signature_observer734.py\n'
OLD_UPLOAD = b'          path: build/ci-verification/windows-ordinary-cause734/public/*\n'
NEW_UPLOAD = b'          path: build/ci-verification/windows-ordinary-signature734/public/*\n'
REVIEWED_EXPECTATIONS_SHA256 = None


def _read_pinned_base_source():
    # No unchecked import/path reread: execute the exact immutable verified bytes.
    # First-stage stat/hash custody is followed by the unchanged native64/128
    # source identity checks in the real controller/worker before network GO.
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
        if view(opened) != view(before):
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
            raise ValueError('Named/descriptor import source differs; numeric-only=' + detail)
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
        return detail
    finally:
        os.close(fd)

try:
    _base_source = _read_pinned_base_source()
except BaseException as error:
    prefix = 'Named/descriptor import source differs; numeric-only='
    text = str(error)
    if type(error) is not ValueError or not text.startswith(prefix) or len(text) > len(prefix) + 2048:
        text = 'Context stat-only refused; numeric operands unavailable: ' + type(error).__name__
    sys.stderr.write(text + '\n')
    raise SystemExit(1)
print(_base_source, flush=True)
raise SystemExit(0)
