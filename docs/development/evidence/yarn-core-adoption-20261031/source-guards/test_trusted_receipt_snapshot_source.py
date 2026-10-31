#!/usr/bin/env python3
"""One private owning SOURCE guard, not JVM execution or a second Yarn parser."""
from __future__ import annotations

import argparse
from pathlib import Path
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--core', required=True, type=Path)
parser.add_argument('--test', required=True, type=Path)
args = parser.parse_args()
CORE = args.core.read_text()
TEST = args.test.read_text()


class TrustedReceiptSnapshotSource(unittest.TestCase):
    def test_trusted_graph_receipts_are_copied_and_not_mutable_through_either_alias(self):
        start = CORE.index('    class CheckedGraph internal constructor(')
        end = CORE.index('    /** Graph-ready lock-only gate;', start)
        graph = CORE[start:end]
        self.assertNotIn('        val inputs: List<InputReceipt>,', graph,
                         'Read-only Kotlin type must not expose the writable trusted constructor list')
        self.assertIn('        inputs: List<InputReceipt>,', graph)
        self.assertIn('val inputs: List<InputReceipt> = Collections.unmodifiableList(ArrayList(inputs))', graph,
                      'An unmodifiable view alone retains a writable constructor alias')
        self.assertIn('inputs.forEach { expected ->', graph)
        self.assertIn('val actual = reader.read(expected.path, expected.cap).receipt', graph)
        self.assertIn('requireSame(expected, actual)', graph)
        self.assertIn('fun requireWorkingLock(workingLock: String): InputReceipt {\n            recheck()', graph)
        self.assertIn('data class InputReceipt(val path: String, val bytes: Int, val sha256: String, internal val cap: Int)', CORE)

        start = TEST.index('    @Test fun checkedInputReceiptsAreAnUnmodifiableOwnedSnapshot() {')
        end = TEST.index('    @Test fun graphReadyReceiptCannotBeReplacedBeforeClosure()', start)
        owning = TEST[start:end]
        self.assertIn('val writable = result.inputs as MutableList<DeclaredYarnClosure.InputReceipt>', owning)
        for operation in ('writable.removeAt(1)', 'writable[0] = writable[0].copy(', 'writable.clear()', 'iterator.remove()'):
            self.assertIn(operation, owning)
        self.assertEqual(4, owning.count('assertThrows(UnsupportedOperationException::class.java)'))
        self.assertIn('val supplied = expected.toMutableList()', owning)
        self.assertIn('DeclaredYarnClosure.CheckedGraph(root, supplied,', owning)
        self.assertIn('supplied.clear()\n        assertEquals(expected, copied.inputs)', owning)
        self.assertIn('rejected("checked-input-changed") { copied.recheck() }', owning)
        self.assertIn('rejected("checked-input-changed") { copied.requireWorkingLock(working) }', owning)
        self.assertNotIn('assume', owning)


unittest.main(argv=['test_trusted_receipt_snapshot_source.py'], verbosity=2)
