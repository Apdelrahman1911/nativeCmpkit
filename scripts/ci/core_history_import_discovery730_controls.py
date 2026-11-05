# SPDX-License-Identifier: Apache-2.0
"""Two genuinely NEW owning import/discovery probes. Never run the old36 methods.

This module is explicitly selected, never test_*.py producer autodiscovery.
The selected core runner executes only these two probe methods. Each target's
ordinary TestLoader discovery may instantiate its declared18 cases, but the
loaded suites/cases are never run. Original loader.errors and unexpected import
exceptions are preserved as bounded observations; no historical pin is guessed.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MAX_DISCOVERY_ERRORS = 256 * 1024


def _cases(suite):
    """Enumerate ordinary loaded cases without running a suite/case or setup."""
    if isinstance(suite, unittest.TestSuite):
        for child in suite:
            yield from _cases(child)
    else:
        yield suite


class CoreHistoryImportDiscovery730Controls(unittest.TestCase):
    def _observe(self, module_name, class_name, prefix):
        path = ROOT / 'scripts/ci' / (module_name + '.py')
        raw = path.read_bytes()
        tree = ast.parse(raw.decode(), filename=str(path))
        self.assertFalse(any(isinstance(node, ast.FunctionDef) and node.name == 'load_tests' for node in tree.body))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
        self.assertEqual(1, len(classes))
        definition = classes[0]
        self.assertEqual(['unittest.TestCase'], [ast.unparse(base) for base in definition.bases])
        self.assertFalse({'__init__', '__call__', 'run', 'id'} &
                         {node.name for node in definition.body if isinstance(node, ast.FunctionDef)})
        declared = [node.name for node in definition.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
        self.assertEqual(18, len(declared))
        self.assertTrue(all(name.startswith(prefix) for name in declared))
        literal = next(node.value for node in tree.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == 'DECLARED_METHODS' for target in node.targets))
        self.assertEqual(tuple(declared), ast.literal_eval(literal))
        record = {'probe': module_name, 'operation': 'OWNING_IMPORT_AND_DISCOVERY_ONLY',
                  'target_source_sha256': hashlib.sha256(raw).hexdigest(), 'target_source_bytes': len(raw),
                  'target_declared_case_count': 18, 'old_test_methods_executed': 0,
                  'native_compiler_consumer_commands': 0, 'loader_errors': [],
                  'forbidden_actions': [], 'import_attempted': False,
                  'fresh_primary_module_before_import': module_name not in sys.modules}

        def emit():
            encoded = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
            if len(encoded) > MAX_DISCOVERY_ERRORS:
                print('CORE730_IMPORT_DISCOVERY ' + json.dumps({
                    'probe': module_name, 'operation': 'OWNING_IMPORT_AND_DISCOVERY_ONLY',
                    'original_error_record_over_bound': True, 'original_error_record_bytes': len(encoded),
                    'original_error_record_sha256': hashlib.sha256(encoded).hexdigest(),
                    'old_test_methods_executed': 0}, sort_keys=True), flush=True)
                raise ValueError('owning-import-discovery-error-record-exceeds256KiB-no-truncation')
            print('CORE730_IMPORT_DISCOVERY ' + encoded.decode(), flush=True)

        def forbidden(*args, **kwargs):
            record['forbidden_actions'].append('process-network-SDK-or-native-action-refused')
            raise AssertionError('No process, network, SDK, or native command admitted by import/discovery-only730')

        if module_name in sys.modules:
            record['refusal'] = 'primary-module-already-imported-no-fresh-import-claimed'
            emit()
            self.fail(record['refusal'])
        loader = unittest.TestLoader()
        with ExitStack() as guards:
            for owner, names in ((subprocess, ('Popen', 'run', 'call', 'check_call', 'check_output', 'getoutput', 'getstatusoutput')),
                                 (os, ('kill', 'killpg', 'system', 'popen', 'fork', 'forkpty', 'posix_spawn', 'posix_spawnp',
                                       'spawnl', 'spawnle', 'spawnlp', 'spawnlpe', 'spawnv', 'spawnve', 'spawnvp', 'spawnvpe',
                                       'execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe')),
                                 (socket, ('socket', 'socketpair', 'create_connection', 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex')),
                                 (unittest.TestSuite, ('run', '__call__')),
                                 (unittest.TestCase, ('run', '__call__'))):
                for name in names:
                    if hasattr(owner, name):
                        guards.enter_context(patch.object(owner, name, forbidden))
            record['import_attempted'] = True
            try:
                loaded = loader.loadTestsFromName(module_name)
            except BaseException as error:
                record['loader_errors'] = list(loader.errors)
                record['original_unexpected_import_exception_type'] = type(error).__name__
                record['original_unexpected_import_exception'] = str(error)
                record['import_succeeded'] = False
                emit()
                raise
        record['loader_errors'] = list(loader.errors)
        cases = list(_cases(loaded))
        if loader.errors:
            record['import_succeeded'] = False
            record['loaded_failure_case_count'] = len(cases)
            originals = [vars(case).get('_exception') for case in cases]
            original = next((error for error in originals if isinstance(error, BaseException)), None)
            if original is not None:
                record['original_loader_exception_type'] = type(original).__name__
                record['original_loader_exception'] = str(original)
            emit()
            if original is not None:
                raise original
            self.fail('owning TestLoader.errors present; original bounded errors recorded without case execution')
        module = sys.modules[module_name]
        self.assertEqual(path.resolve(), Path(module.__file__).resolve())
        self.assertEqual(ROOT.resolve(), Path(module.TREE).resolve())
        self.assertIs(type(module.DECLARED_METHODS), tuple)
        self.assertEqual(tuple(declared), module.DECLARED_METHODS)
        self.assertEqual(18, len(cases))
        self.assertEqual([module_name + '.' + class_name + '.' + name for name in sorted(declared)],
                         sorted(case.id() for case in cases))
        counters = getattr(module, 'COUNTERS', {})
        self.assertIs(type(counters), dict)
        for key in ('existing_accepted_test_methods_selected', 'native_invocations', 'fresh_owned_models'):
            if key in counters:
                self.assertEqual(0, counters[key])
        self.assertEqual([], record['forbidden_actions'])
        record['import_succeeded'] = True
        record['ordinary_old_cases_discovered_not_executed'] = len(cases)
        record['original_loader_errors_empty'] = True
        record['counter_observations_only'] = {key: counters[key] for key in
            ('existing_accepted_test_methods_selected', 'native_invocations', 'fresh_owned_models') if key in counters}
        emit()

    def test01_pre_reporter_fail_fast_import_and_discovery_only(self):
        self._observe('test_android_camera_pre_reporter_fail_fast', 'PreReporterFailFastNewOnlyTests', 'test_ff')

    def test02_startup_readiness_import_and_discovery_only(self):
        self._observe('test_android_camera_startup_readiness', 'CameraStartupReadinessNewOnlyTests', 'test_sr')
