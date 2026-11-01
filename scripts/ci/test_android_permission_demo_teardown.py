"""Owning teardown source guards and bounded Python models; never Kotlin/native executions."""
from dataclasses import dataclass
from pathlib import Path
import re
import unittest

import android_permission_demo as demo

ROOT = Path(__file__).resolve().parents[2]


def code_block(source, marker):
    """Read one brace-balanced source block, ignoring comments and quoted braces.

    This is a narrow source-review utility, not a Kotlin parser/compiler.
    """
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    if marker not in source:
        raise AssertionError("Missing owning source block: " + marker)
    start = source.index("{", source.index(marker) + len(marker))
    depth, quote, escaped = 1, None, False
    for index in range(start + 1, len(source)):
        char = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1:index]
    raise AssertionError("Unterminated owning source block: " + marker)


def compact(source):
    return re.sub(r"\s+", " ", source).strip()


class AndroidPermissionDemoTeardownSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / demo.APPLICATION_KOTLIN / "PermissionDemoActivity.kt").read_text()

    def test_finish_attempts_cleanup_then_finalizes_and_rethrows_the_retained_failure(self):
        finish = compact(code_block(self.source, 'if (operation == "finish")'))
        self.assertIn("try { closeOwnedActivity() } catch (failure: Throwable) { recordCleanupFailure(failure) } finally {", finish)
        self.assertIn("try { finish() } catch (failure: Throwable) { recordCleanupFailure(failure) }", finish)
        self.assertTrue(finish.endswith("cleanupFailure?.let { throw it } return"))
        self.assertLess(finish.index("closeOwnedActivity()"), finish.index("finish()"))
        self.assertLess(finish.index("finish()"), finish.index("cleanupFailure?.let { throw it }"))

    def test_destroy_attempts_cleanup_clears_active_and_calls_super_before_rethrow(self):
        destroy = compact(code_block(self.source, "override fun onDestroy()"))
        self.assertIn("try { closeOwnedActivity() } catch (failure: Throwable) { recordCleanupFailure(failure) } finally {", destroy)
        self.assertIn("if (active === this) active = null", destroy)
        self.assertIn("try { super.onDestroy() } catch (failure: Throwable) { recordCleanupFailure(failure) }", destroy)
        self.assertTrue(destroy.endswith("cleanupFailure?.let { throw it }"))
        self.assertLess(destroy.index("closeOwnedActivity()"), destroy.index("active = null"))
        self.assertLess(destroy.index("active = null"), destroy.index("super.onDestroy()"))
        self.assertLess(destroy.index("super.onDestroy()"), destroy.index("cleanupFailure?.let { throw it }"))

    def test_read_assertion_and_owned_rows_have_independent_failure_scopes_without_cancel_or_wait(self):
        cleanup = compact(code_block(self.source, "private fun closeOwnedActivity()"))
        self.assertEqual(
            "try { check(activeReads == 0) } catch (failure: Throwable) { recordCleanupFailure(failure) } "
            "try { closeOwnedSeeds() } catch (failure: Throwable) { recordCleanupFailure(failure) }",
            cleanup,
        )
        for substitute in ("cancel(", "cancelAndJoin", ".join(", "runBlocking"):
            self.assertNotIn(substitute, self.source)
        # The field's genuine zero initializer is not a runtime reset. Refuse
        # assignment inside every current lifecycle/control/read/cleanup path.
        for marker in ("override fun onCreate(", "fun perform(", "private fun received(",
            "private fun closeOwnedActivity()", "private fun closeOwnedSeeds()", "override fun onDestroy()"):
            self.assertNotRegex(code_block(self.source, marker), r"\bactiveReads\s*=\s*0\b")
        read = compact(code_block(self.source, "private fun received("))
        self.assertIn("activeReads++", read)
        self.assertIn("finally { activeReads-- }", read)
        self.assertIn("file.readByteArray(maxBytes = 65536)", read)
        self.assertIn("assertOwnedAndUnchanged(source)", read)

    def test_process_retained_failure_survives_active_clear_and_cannot_be_reset_on_create(self):
        record = compact(code_block(self.source, "private fun recordCleanupFailure("))
        self.assertEqual("cleanupFailed = true cleanupFailure = appendFailure(cleanupFailure, failure)", record)
        companion = compact(code_block(self.source, "companion object"))
        self.assertIn("@Volatile private var cleanupFailure: Throwable? = null", companion)
        created = compact(code_block(self.source, "override fun onCreate("))
        self.assertIn("check(!cleanupFailed && cleanupFailure == null)", created)
        self.assertNotIn("cleanupFailed = false", created)
        self.assertNotIn("cleanupFailure = null", created)
        self.assertLess(created.index("check(!cleanupFailed"), created.index("active = this"))
        for marker in ('if (operation == "finish")', "override fun onDestroy()"):
            self.assertNotIn("cleanupFailure = null", code_block(self.source, marker))

    def test_row_content_removal_and_later_rows_aggregate_without_masking_each_other(self):
        cleanup = compact(code_block(self.source, "private fun closeOwnedSeeds()"))
        self.assertIn("var firstFailure: Throwable? = null", cleanup)
        self.assertIn("for ((kind, seed) in seeds.toMap())", cleanup)
        self.assertIn("if (seed.published) { try { assertOwnedAndUnchanged(seed) } catch (failure: Throwable) { firstFailure = appendFailure(firstFailure, failure) } }", cleanup)
        self.assertIn("try { assertOwnedIdentity(seed) check(contentResolver.delete(seed.uri, null, null) == 1) seeds.remove(kind) } catch (failure: Throwable) { firstFailure = appendFailure(firstFailure, failure) }", cleanup)
        self.assertEqual(3, cleanup.count("firstFailure = appendFailure(firstFailure, failure)"))
        self.assertTrue(cleanup.endswith("firstFailure?.let { throw it }"))
        self.assertNotIn("contentFailure?.let { throw it }", cleanup)
        self.assertNotIn("if (firstFailure == null) firstFailure = failure", cleanup)

    def test_exact_identity_failure_skips_that_row_and_deletion_requires_a_fresh_identity(self):
        cleanup = compact(code_block(self.source, "private fun closeOwnedSeeds()"))
        self.assertIn("try { assertOwnedIdentity(seed) } catch (failure: Throwable) { firstFailure = appendFailure(firstFailure, failure) continue }", cleanup)
        self.assertEqual(2, cleanup.count("assertOwnedIdentity(seed)"))
        self.assertIn("assertOwnedIdentity(seed) check(contentResolver.delete(seed.uri, null, null) == 1)", cleanup)
        identity = compact(code_block(self.source, "private fun assertOwnedIdentity("))
        self.assertIn("check(cursor.count == 1 && cursor.moveToFirst())", identity)
        self.assertIn("check(cursor.getString(0) == packageName && cursor.getString(1) == seed.name)", identity)
        insert = compact(code_block(self.source, "private fun insertOwned("))
        self.assertLess(insert.index("seeds[kind] = seed"), insert.index("openOutputStream"))

    def test_aggregate_preserves_distinct_failure_objects_and_refuses_self_suppression(self):
        aggregate = compact(code_block(self.source, "private fun appendFailure("))
        self.assertEqual(
            "if (firstFailure == null) return failure "
            "if (firstFailure !== failure) firstFailure.addSuppressed(failure) return firstFailure",
            aggregate,
        )


class ModelFailure(Exception):
    """Identity-bearing Python model error; never an observed Android error."""
    def __init__(self, label):
        super().__init__(label)
        self.suppressed = []


def model_append(first, failure):
    if first is None:
        return failure
    if first is not failure:
        first.suppressed.append(failure)
    return first


def model_failure_objects(first):
    result = []

    def visit(failure):
        if failure is not None and all(failure is not value for value in result):
            result.append(failure)
            for child in failure.suppressed:
                visit(child)

    visit(first)
    return result


@dataclass
class ModelRow:
    published: bool = True
    admission_failure: ModelFailure | None = None
    content_failure: ModelFailure | None = None
    deletion_identity_failure: ModelFailure | None = None
    deletion_failure: ModelFailure | None = None


class TeardownModel:
    """Deterministic failure-order model, not a native executor or removal proof."""
    def __init__(self, rows, active_reads=0, read_failure=None):
        self.rows = dict(rows)
        self.active_reads = active_reads
        self.read_failure = read_failure
        self.cleanup_failed = False
        self.failure = None
        self.active = True
        self.events = []

    def record(self, failure):
        self.cleanup_failed = True
        self.failure = model_append(self.failure, failure)

    def close_rows(self):
        first = None
        for kind, row in dict(self.rows).items():
            self.events.append((kind, "admit-identity"))
            if row.admission_failure is not None:
                first = model_append(first, row.admission_failure)
                continue
            if row.published:
                self.events.append((kind, "content"))
                if row.content_failure is not None:
                    first = model_append(first, row.content_failure)
            self.events.append((kind, "delete-identity"))
            if row.deletion_identity_failure is not None:
                first = model_append(first, row.deletion_identity_failure)
                continue
            self.events.append((kind, "delete"))
            if row.deletion_failure is not None:
                first = model_append(first, row.deletion_failure)
            else:
                del self.rows[kind]
        return first

    def teardown(self, operation, finalizer_failure=None):
        assert operation in ("finish", "destroy")
        self.events.append(("activity", "assert-active-reads"))
        if self.active_reads != 0:
            self.record(self.read_failure or ModelFailure("active-reads"))
        row_failure = self.close_rows()
        if row_failure is not None:
            self.record(row_failure)
        if operation == "destroy":
            self.events.append(("activity", "clear-active"))
            self.active = False
        self.events.append(("activity", operation + "-finalizer"))
        if finalizer_failure is not None:
            self.record(finalizer_failure)
        if self.failure is not None:
            raise self.failure


class AndroidPermissionDemoTeardownModelTest(unittest.TestCase):
    def test_nonzero_read_still_attempts_all_owned_rows_and_remains_failed_after_a_later_zero(self):
        read = ModelFailure("original-read-refusal")
        model = TeardownModel({"document": ModelRow(), "image": ModelRow()}, active_reads=1, read_failure=read)
        with self.assertRaises(ModelFailure) as first:
            model.teardown("finish")
        self.assertIs(read, first.exception)
        self.assertEqual({}, model.rows)
        self.assertIn(("document", "delete"), model.events)
        self.assertIn(("image", "delete"), model.events)
        self.assertEqual(("activity", "finish-finalizer"), model.events[-1])
        self.assertTrue(model.cleanup_failed)
        # Synthetic later-zero observation is not cancellation/descriptor settlement.
        model.active_reads = 0
        with self.assertRaises(ModelFailure) as later:
            model.teardown("destroy")
        self.assertIs(read, later.exception)
        self.assertFalse(model.active)
        self.assertTrue(model.cleanup_failed)

    def test_original_content_delete_later_row_and_finalizer_failures_all_keep_their_identities(self):
        read, content, deletion, later, finalizer = [ModelFailure(name) for name in
            ("read", "document-content", "document-delete", "image-content", "finish-finalizer")]
        model = TeardownModel({"document": ModelRow(content_failure=content, deletion_failure=deletion),
            "image": ModelRow(content_failure=later)}, active_reads=1, read_failure=read)
        with self.assertRaises(ModelFailure) as result:
            model.teardown("finish", finalizer)
        self.assertIs(read, result.exception)
        self.assertEqual([read, content, deletion, later, finalizer], model_failure_objects(model.failure))
        self.assertEqual({"document"}, set(model.rows))
        self.assertIn(("image", "delete"), model.events)
        self.assertTrue(model.cleanup_failed)

    def test_foreign_or_unknown_initial_identity_never_admits_read_or_delete_but_next_row_is_attempted(self):
        identity = ModelFailure("unknown-owner-or-name")
        model = TeardownModel({"document": ModelRow(admission_failure=identity), "image": ModelRow()})
        with self.assertRaises(ModelFailure):
            model.teardown("destroy")
        self.assertNotIn(("document", "content"), model.events)
        self.assertNotIn(("document", "delete-identity"), model.events)
        self.assertNotIn(("document", "delete"), model.events)
        self.assertIn(("image", "delete"), model.events)
        self.assertEqual({"document"}, set(model.rows))
        self.assertFalse(model.active)
        self.assertTrue(model.cleanup_failed)

    def test_identity_change_after_content_refuses_delete_and_retains_both_failures(self):
        content, identity = ModelFailure("changed-content"), ModelFailure("changed-before-delete")
        model = TeardownModel({"document": ModelRow(content_failure=content, deletion_identity_failure=identity),
            "image": ModelRow(published=False)})
        with self.assertRaises(ModelFailure) as result:
            model.teardown("finish")
        self.assertIs(content, result.exception)
        self.assertEqual([content, identity], model_failure_objects(model.failure))
        self.assertNotIn(("document", "delete"), model.events)
        self.assertNotIn(("image", "content"), model.events)
        self.assertIn(("image", "delete"), model.events)
        self.assertEqual({"document"}, set(model.rows))

    def test_destroy_finalizer_error_is_retained_after_active_clears_without_replacing_original(self):
        deletion, finalizer = ModelFailure("row-delete"), ModelFailure("super-destroy")
        model = TeardownModel({"image": ModelRow(deletion_failure=deletion)})
        with self.assertRaises(ModelFailure) as result:
            model.teardown("destroy", finalizer)
        self.assertIs(deletion, result.exception)
        self.assertFalse(model.active)
        self.assertEqual([deletion, finalizer], model_failure_objects(model.failure))
        self.assertEqual([("activity", "clear-active"), ("activity", "destroy-finalizer")], model.events[-2:])
        self.assertTrue(model.cleanup_failed)
        self.assertEqual({"image"}, set(model.rows))

    def test_success_control_and_same_object_append_do_not_fabricate_or_clear_a_failure(self):
        model = TeardownModel({"document": ModelRow(published=False), "image": ModelRow()})
        model.teardown("finish")
        self.assertEqual({}, model.rows)
        self.assertFalse(model.cleanup_failed)
        self.assertIsNone(model.failure)
        self.assertTrue(model.active)  # finish is not modeled as synchronous destruction.
        model.teardown("destroy")
        self.assertFalse(model.active)
        failure = ModelFailure("same-object")
        model.record(failure)
        model.record(failure)
        self.assertIs(failure, model.failure)
        self.assertEqual([], failure.suppressed)
        self.assertTrue(model.cleanup_failed)


if __name__ == "__main__":
    unittest.main()
