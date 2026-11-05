# SPDX-License-Identifier: Apache-2.0
"""NEW9 owning identity recovery controls; synthetic only, never Windows/native.

Only the new observer is imported. DLL/file-handle metadata is mocked; temporary
files are owning test fixtures. No original8/12/Stop suite, network, dependency,
Gradle/Java/native or real Windows Job runs. The original759 failure remains.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import copy
import ctypes
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import windows_ordinary_dependency_observer742 as observer

UNCHANGED_FUNCTION_HASHES = {'snapshot_sources': '49bc9513728757a45ad36fba4c37ed86f5aa747216916b5613d06b9c65de7b2d', 'coordinate_url': '2f71ce79aef2ff27cdd6e4e8b167a6c0f1d8e595e935da98939628c60d3bb29b', 'validate_request': '131f4e1ff951af49c58f33a2bf1eb97f53656273e55a12a65afc7f8a775ca238', 'observe_one': 'bfb86b2a5cfc47f73a3d9510698eb99fa76e010c4e2e0e1af37fb32e1a06698a', 'worker': 'a8e9af1eb68246b57d8c7dcef7782fd6577a51791219f4da489437370f41dd17', 'verify_worker_job': '2e8d6577b3566ac4aacec29dc0dbf10022256232186c74d6d19ed4fea5e244cd', 'assigned_go': '8cff83ced0c4a77798c6023d8314422df402a1ef5c3c146fd132ce7239ea53e7', 'controller': 'd60764a6cee1728dec232ad4447943933ad85e666e62da59a8b8581c8799a1a5', 'main': '4a29b60bf11c434b14a3f4159118a619917802dd1d8446f7ca4aedccff6af0f5', 'directory_pin': 'c888776ba104a55f8265fc9692af04a60d81d50157ecc9786dd30af445ae8fe5', 'create_owned': '33e6edb96d86127f2bc59b3b9d0fd8f78b7618e5206ded3fb3e5a05a36765df1', 'manual_context': '8305069b10bd89b2288517286e30311ddd90760462540803964f9aacb8bd937d', 'safe_environment': 'b4c29ce2dc15d2bf78acb09300aae4493beb7c9360065fc988c9c1b296d5814b', 'load_plan': '5414dbacb2e4252344b7bec6d5543032dff746d01a0afd3baa8404ac4b02309b'}
EXPECTED_OBSERVER_SHA256 = 'd73c253d6ffe75ed454f14e2888aaacf9b6dd6e6af5d09e2811c71c781d9ada6'


def definition(source, name):
    nodes = [node for node in ast.parse(source).body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError('One owning source definition')
    node = nodes[0]
    return '\n'.join(source.splitlines()[node.lineno - 1:node.end_lineno])


def native_record(size=7):
    return {'volume_serial_64': 0xFEDCBA9876543210,
            'file_id_128': (0xDEADBEEF12345678 << 64) | 0xABCDEF0123456789,
            'file_attributes': 0x20, 'number_of_links': 1, 'file_size': size,
            'creation_time_100ns': 133700000000000000,
            'last_write_time_100ns': 133700000000000010,
            'change_time_100ns': 133700000000000020,
            'directory': 0, 'delete_pending': 0}


class FakeFunction:
    def __init__(self, operation):
        self.operation = operation
        self.argtypes = self.restype = None

    def __call__(self, *args):
        return self.operation(*args)


class FakeKernel:
    BORROWED = 734
    def __init__(self, record, named=None, borrowed=None):
        self.record = dict(record)
        self.named_records = list(named or [record])
        self.borrowed_records = list(borrowed or [record])
        self.named_count = self.borrowed_count = 0
        self.handles = {}
        self.events = []
        self.fail_open = self.fail_close = False
        self.fail_query = self.fail_borrowed_query = None
        self.file_type = 1
        self.CreateFileW = FakeFunction(self.open)
        self.GetFileType = FakeFunction(self.kind)
        self.GetFileInformationByHandleEx = FakeFunction(self.query)
        self.CloseHandle = FakeFunction(self.close)

    def select(self, records, index):
        return dict(records[min(index, len(records) - 1)])

    def open(self, *args):
        self.events.append(('open', args))
        if self.fail_open:
            return ctypes.c_void_p(-1).value
        handle = 2000 + self.named_count
        self.handles[handle] = self.select(self.named_records, self.named_count)
        self.named_count += 1
        return handle

    def get_osfhandle(self, descriptor):
        self.events.append(('borrow', descriptor))
        self.handles[self.BORROWED] = self.select(self.borrowed_records, self.borrowed_count)
        self.borrowed_count += 1
        return self.BORROWED

    def kind(self, handle):
        self.events.append(('type', handle))
        return self.file_type

    def query(self, handle, information_class, pointer, size):
        self.events.append(('query', handle, information_class, size))
        if self.fail_query == information_class or (handle == self.BORROWED and self.fail_borrowed_query == information_class):
            return 0
        row = self.handles[handle]
        target = pointer._obj
        if information_class == 0:
            target.CreationTime = row['creation_time_100ns']
            target.LastAccessTime = 999999  # Deliberately excluded volatile read access time.
            target.LastWriteTime = row['last_write_time_100ns']
            target.ChangeTime = row['change_time_100ns']
            target.FileAttributes = row['file_attributes']
        elif information_class == 1:
            target.AllocationSize = row['file_size'] + 4096
            target.EndOfFile = row['file_size']
            target.NumberOfLinks = row['number_of_links']
            target.DeletePending = row['delete_pending']
            target.Directory = row['directory']
        elif information_class == 18:
            target.VolumeSerialNumber = row['volume_serial_64']
            target.FileId[:] = row['file_id_128'].to_bytes(16, 'little')
        else:
            raise AssertionError('No legacy/truncating fallback query')
        return 1

    def close(self, handle):
        self.events.append(('close', handle))
        if handle == self.BORROWED:
            raise AssertionError('Borrowed CRT handle must never be CloseHandle-owned')
        return 0 if self.fail_close else 1


@contextmanager
def kernel(fake):
    with mock.patch.dict(sys.modules, {'msvcrt': SimpleNamespace(get_osfhandle=fake.get_osfhandle)}):
        with mock.patch.object(observer.ctypes, 'WinDLL', return_value=fake, create=True) as dll:
            yield fake
            if dll.call_count:
                dll.assert_called_with('kernel32', use_last_error=True)


def altered_stat(value, changes):
    values = {field: getattr(value, field) for field in observer.SOURCE_FIELDS}
    values['st_file_attributes'] = getattr(value, 'st_file_attributes', 0)
    values.update(changes)
    return SimpleNamespace(**values)


@contextmanager
def descriptor_view_different():
    original = os.fstat
    def own_view(descriptor):
        value = original(descriptor)
        return altered_stat(value, {'st_dev': value.st_dev + 101, 'st_ino': value.st_ino + 303,
                                    'st_ctime_ns': value.st_ctime_ns + 707})
    with mock.patch.object(observer.os, 'fstat', side_effect=own_view):
        yield


@contextmanager
def named_change(path, field, increment=1, from_call=3):
    original = Path.lstat
    calls = [0]
    def changed(current, *args, **kwargs):
        value = original(current, *args, **kwargs)
        if current == path:
            calls[0] += 1
            if calls[0] >= from_call:
                return altered_stat(value, {field: getattr(value, field, 0) + increment})
        return value
    with mock.patch.object(Path, 'lstat', changed):
        yield


class WindowsObserverIdentityRecovery734Tests(unittest.TestCase):
    def temporary(self):
        return tempfile.TemporaryDirectory(prefix='identity734-')

    def fixture(self, directory, payload=b'payload'):
        root = Path(directory)
        path = root / 'source.bin'
        path.write_bytes(payload)
        return root, path

    def test_new_scope_original_native_protocol_and_full_POSIXstat7_preserved(self):
        source = Path(observer.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), EXPECTED_OBSERVER_SHA256)
        text = source.decode()
        self.assertEqual(observer.SOURCE_FIELDS,
                         ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
        for name, expected in UNCHANGED_FUNCTION_HASHES.items():
            with self.subTest(unchanged=name):
                self.assertEqual(hashlib.sha256(definition(text, name).encode()).hexdigest(), expected)
        self.assertEqual(observer.PLAN_SHA256, 'e3d86c27cbb88650b306410c01a07b094c8166552f45f8b5ef1718b0cfaf5133')
        self.assertEqual(observer.CHOICE, 'windows-ordinary-dependency-observation1')
        self.assertEqual(observer.NO_ADMISSION['reviewed_expectations_authority'], None)
        self.assertTrue(observer.NO_ADMISSION['observations_are_untrusted'])
        self.assertFalse(observer.NO_ADMISSION['native_or_ordinary_consumer_qualified'])
        for name, called in (('read_regular', '_read_windows_regular'), ('write_exclusive', '_write_windows_exclusive')):
            tree = ast.parse(definition(text, name)).body[0]
            dispatch = next(node for node in tree.body if isinstance(node, ast.If))
            self.assertEqual(ast.unparse(dispatch.test), "os.name == 'nt'")
            self.assertEqual(dispatch.body[0].value.func.id, called)

    def test_POSIX_reader_writer_full_crossstat7_reparse_shared_bounds_and_ancestor_refusals(self):
        self.assertNotEqual(os.name, 'nt', 'These controls never run a real Windows host/API')
        with self.temporary() as directory:
            root, path = self.fixture(directory)
            payload, row = observer.read_regular(root, path.name)
            self.assertEqual(payload, b'payload')
            self.assertEqual(len(row['stat_identity']), 7)
            original = os.fstat
            for field in observer.SOURCE_FIELDS:
                with self.subTest(field=field):
                    def different(fd, field=field):
                        value = original(fd)
                        return altered_stat(value, {field: getattr(value, field) + 1})
                    with mock.patch.object(observer.os, 'fstat', side_effect=different):
                        with self.assertRaises(observer.ObservationRefusal):
                            observer.read_regular(root, path.name)
            with self.assertRaises(observer.ObservationRefusal):
                observer.read_regular(root, path.name, limit=6)
            with named_change(path, 'st_file_attributes', 1024, from_call=1):
                with self.assertRaises(observer.ObservationRefusal):
                    observer.read_regular(root, path.name)
            os.link(path, root / 'shared.bin')
            with self.assertRaises(observer.ObservationRefusal):
                observer.read_regular(root, path.name)
            (root / 'shared.bin').unlink()
            pins = {root: observer.directory_pin(root)}
            result = observer.write_exclusive(root, 'new.bin', b'new', pins)
            self.assertEqual(result['sha256'], hashlib.sha256(b'new').hexdigest())
            with self.assertRaises(FileExistsError):
                observer.write_exclusive(root, 'new.bin', b'bad', pins)
            self.assertEqual((root / 'new.bin').read_bytes(), b'new')
            original_pin = observer.directory_pin
            count = [0]
            def changed_parent(current):
                pin = original_pin(current)
                count[0] += 1
                return pin if count[0] == 1 else (pin[0], pin[1] + 1, *pin[2:])
            with mock.patch.object(observer, 'directory_pin', side_effect=changed_parent):
                with self.assertRaises(observer.ObservationRefusal):
                    observer.read_regular(root, path.name)

    def test_Win32_full128_ID_volume64_ABI_and_owned_vs_borrowed_handle_lifecycle(self):
        record = native_record()
        fake = FakeKernel(record)
        with kernel(fake):
            native = observer._Win32FileIdentity()
            self.assertEqual([ctypes.sizeof(native.BasicInfo), ctypes.sizeof(native.StandardInfo), ctypes.sizeof(native.IdInfo)],
                             [40, 24, 24])
            expected = tuple(record[field] for field in observer.WIN32_SOURCE_FIELDS)
            self.assertEqual(native.named(Path('/absolute/mock.bin'), 100), expected)
            self.assertEqual(native.borrowed(93, 100), expected)
        self.assertEqual([event[2:] for event in fake.events if event[0] == 'query'],
                         [(0, 40), (1, 24), (18, 24)] * 2)
        self.assertEqual([event[1] for event in fake.events if event[0] == 'close'], [2000])
        open_arguments = next(event[1] for event in fake.events if event[0] == 'open')
        self.assertEqual(open_arguments[1:], (0x80, 0x7, None, 3, 0x00200000 | 0x02000000, None))
        self.assertGreater(expected[0], 2 ** 32)
        self.assertGreater(expected[1], 2 ** 64)
        for changes in ({'file_attributes': 0x420}, {'file_attributes': 0x30}, {'directory': 1},
                        {'delete_pending': 1}, {'number_of_links': 2}, {'file_size': 101},
                        {'creation_time_100ns': -1}, {'file_size': 0}):
            with self.subTest(shape=changes), kernel(FakeKernel(dict(record, **changes))):
                with self.assertRaises(observer.ObservationRefusal):
                    observer._Win32FileIdentity().named(Path('/absolute/mock.bin'), 100)

    def test_Windows_reader_separate_python_views_do_not_waive_native_or_own_stat_custody(self):
        with self.temporary() as directory:
            root, path = self.fixture(directory)
            fake = FakeKernel(native_record())
            with kernel(fake), descriptor_view_different():
                payload, row = observer._read_windows_regular(root, path.name)
            self.assertEqual(payload, b'payload')
            self.assertNotEqual(row['stat_identity'], row['descriptor_stat_identity'])
            self.assertEqual(row['windows_file_identity']['fields'], list(observer.WIN32_SOURCE_FIELDS))
            self.assertEqual(int(row['windows_file_identity']['values'][1]), native_record()['file_id_128'])
            for field in observer.SOURCE_FIELDS:
                original = os.fstat
                count = [0]
                def descriptor_drift(fd, field=field):
                    value = original(fd)
                    count[0] += 1
                    return altered_stat(value, {field: getattr(value, field) + 1}) if count[0] > 1 else value
                with self.subTest(own_fd_stat7=field), kernel(FakeKernel(native_record())):
                    with mock.patch.object(observer.os, 'fstat', side_effect=descriptor_drift):
                        with self.assertRaises(observer.ObservationRefusal):
                            observer._read_windows_regular(root, path.name)
            for field in observer.SOURCE_FIELDS:
                with self.subTest(own_named_stat7=field), kernel(FakeKernel(native_record())):
                    with named_change(path, field, from_call=3):
                        with self.assertRaises(observer.ObservationRefusal):
                            observer._read_windows_regular(root, path.name)

    def test_Windows_reader_every_native_field_high_ID_and_fresh_after_read_close_drift_refused(self):
        with self.temporary() as directory:
            root, path = self.fixture(directory)
            base = native_record()
            for field in observer.WIN32_SOURCE_FIELDS:
                changed = dict(base)
                changed[field] += (1 << 100) if field == 'file_id_128' else 1
                with self.subTest(native_field=field):
                    with kernel(FakeKernel(base, borrowed=[changed])):
                        with self.assertRaises(observer.ObservationRefusal):
                            observer._read_windows_regular(root, path.name)
            changed = dict(base, file_id_128=base['file_id_128'] ^ (1 << 100))
            for phase, fake in (
                ('descriptor-after-read', FakeKernel(base, borrowed=[base, changed])),
                ('named-during-read', FakeKernel(base, named=[base, changed])),
                ('named-after-close', FakeKernel(base, named=[base, base, changed]))):
                with self.subTest(phase=phase), kernel(fake):
                    with self.assertRaises(observer.ObservationRefusal):
                        observer._read_windows_regular(root, path.name)
                self.assertFalse(any(event == ('close', fake.BORROWED) for event in fake.events))

    def test_Win32_open_query_close_failures_fail_closed_and_keep_primary_without_borrowed_close(self):
        for query in (0, 1, 18):
            fake = FakeKernel(native_record())
            fake.fail_query = query
            with self.subTest(query=query), kernel(fake):
                with self.assertRaises(observer.ObservationRefusal):
                    observer._Win32FileIdentity().named(Path('/absolute/mock.bin'), 100)
            self.assertEqual([event for event in fake.events if event[0] == 'close'], [('close', 2000)])
        fake = FakeKernel(native_record())
        fake.fail_open = True
        with kernel(fake):
            with self.assertRaises(observer.ObservationRefusal):
                observer._Win32FileIdentity().named(Path('/absolute/mock.bin'), 100)
        self.assertFalse(any(event[0] in ('query', 'close') for event in fake.events))
        fake = FakeKernel(native_record())
        fake.fail_close = True
        with kernel(fake):
            with self.assertRaises(observer.ObservationRefusal):
                observer._Win32FileIdentity().named(Path('/absolute/mock.bin'), 100)
        fake = FakeKernel(native_record())
        fake.fail_query, fake.fail_close = 18, True
        with kernel(fake):
            with self.assertRaises(observer.ObservationRefusal) as failure:
                observer._Win32FileIdentity().named(Path('/absolute/mock.bin'), 100)
        self.assertIn('query failed: 18', str(failure.exception))
        self.assertEqual(len(getattr(failure.exception, '__notes__', [])), 1)
        fake = FakeKernel(native_record())
        fake.fail_query = 18
        with kernel(fake):
            with self.assertRaises(observer.ObservationRefusal):
                observer._Win32FileIdentity().borrowed(93, 100)
        self.assertFalse(any(event[0] == 'close' for event in fake.events))

    def test_Windows_exclusive_write_complete_readback_and_explicit_owning_close_time_interval(self):
        with self.temporary() as directory:
            root = Path(directory)
            pins = {root: observer.directory_pin(root)}
            before = native_record()
            after = dict(before, last_write_time_100ns=before['last_write_time_100ns'] + 10,
                         change_time_100ns=before['change_time_100ns'] + 20)
            fake = FakeKernel(before, named=[before, after], borrowed=[before, before, after, after])
            with kernel(fake), descriptor_view_different():
                result = observer._write_windows_exclusive(root, 'new.bin', b'payload', pins)
            self.assertEqual((root / 'new.bin').read_bytes(), b'payload')
            custody = result['windows_write_close_custody']
            self.assertTrue(custody['full_final_path_descriptor_native_custody'])
            self.assertTrue(custody['only_forward_time_fields_changed_across_owning_close_interval'])
            self.assertTrue(custody['forward_time_transition_does_not_establish_actor_or_cause'])
            self.assertTrue(custody['exact_final_complete_content_readback'])
            self.assertEqual(custody['changed_native_time_fields'], ['last_write_time_100ns', 'change_time_100ns'])
            self.assertFalse(any(event == ('close', fake.BORROWED) for event in fake.events))
            with kernel(FakeKernel(native_record())):
                with self.assertRaises(FileExistsError):
                    observer._write_windows_exclusive(root, 'new.bin', b'changed', pins)
            with kernel(FakeKernel(native_record(0))):
                empty = observer._write_windows_exclusive(root, 'empty.bin', b'', pins)
            self.assertEqual(empty['bytes'], 0)
            self.assertEqual((root / 'empty.bin').read_bytes(), b'')
            with kernel(FakeKernel(native_record(0))):
                with self.assertRaises(observer.ObservationRefusal):
                    observer._read_windows_regular(root, 'empty.bin')

    def test_Windows_exclusive_write_non_time_ID_attrs_creation_backwards_time_content_parent_refused(self):
        for field in ('volume_serial_64', 'file_id_128', 'file_attributes', 'number_of_links', 'file_size', 'creation_time_100ns'):
            with self.subTest(non_time=field), self.temporary() as directory:
                root = Path(directory);pins = {root: observer.directory_pin(root)};before = native_record();after = dict(before)
                after[field] += (1 << 100) if field == 'file_id_128' else 1
                with kernel(FakeKernel(before, named=[before, after], borrowed=[before, before, after, after])):
                    with self.assertRaises(observer.ObservationRefusal):
                        observer._write_windows_exclusive(root, 'new.bin', b'payload', pins)
                self.assertTrue((root / 'new.bin').is_file(), 'Failed own output retained, never recursive cleanup')
        for field in ('last_write_time_100ns', 'change_time_100ns'):
            with self.subTest(backwards=field), self.temporary() as directory:
                root = Path(directory);pins = {root: observer.directory_pin(root)};before = native_record();after = dict(before)
                after[field] -= 1
                with kernel(FakeKernel(before, named=[before, after], borrowed=[before, before, after, after])):
                    with self.assertRaises(observer.ObservationRefusal):
                        observer._write_windows_exclusive(root, 'new.bin', b'payload', pins)
        with self.temporary() as directory:
            root = Path(directory);pins = {root: observer.directory_pin(root)}
            original_read = observer._read_windows_regular
            def wrong_content(*args, **kwargs):
                payload, row = original_read(*args, **kwargs)
                return b'X' * len(payload), row
            with kernel(FakeKernel(native_record())):
                with mock.patch.object(observer, '_read_windows_regular', side_effect=wrong_content):
                    with self.assertRaises(observer.ObservationRefusal):
                        observer._write_windows_exclusive(root, 'content.bin', b'payload', pins)
            pins[root] = (pins[root][0], pins[root][1] + 1, *pins[root][2:])
            with kernel(FakeKernel(native_record())):
                with self.assertRaises(observer.ObservationRefusal):
                    observer._write_windows_exclusive(root, 'foreign-parent.bin', b'payload', pins)
            self.assertFalse((root / 'foreign-parent.bin').exists())

    def test_Windows_read_write_query_refusals_close_owned_CRT_fds_and_never_clear_failed_outputs(self):
        with self.temporary() as directory:
            root, path = self.fixture(directory)
            for operation in ('read', 'write'):
                fake = FakeKernel(native_record());fake.fail_borrowed_query = 18
                opened = [];real_open = os.open;real_fstat = os.fstat
                def tracked_open(*args, **kwargs):
                    fd = real_open(*args, **kwargs);opened.append(fd);return fd
                with self.subTest(operation=operation), kernel(fake):
                    with mock.patch.object(observer.os, 'open', side_effect=tracked_open):
                        with self.assertRaises(observer.ObservationRefusal):
                            if operation == 'read':
                                observer._read_windows_regular(root, path.name)
                            else:
                                observer._write_windows_exclusive(root, 'failed.bin', b'payload',
                                                                  {root: observer.directory_pin(root)})
                self.assertEqual(len(opened), 1, 'Failure occurs after the sole owning CRT descriptor opens')
                for descriptor in opened:
                    with self.assertRaises(OSError):
                        real_fstat(descriptor)
                self.assertFalse(any(event == ('close', fake.BORROWED) for event in fake.events))
            self.assertEqual(path.read_bytes(), b'payload')
            self.assertTrue((root / 'failed.bin').exists())
