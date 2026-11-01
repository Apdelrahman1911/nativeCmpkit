"""Eight source/negative-mutation guards only; never SDK/build/native evidence.

The public SDK37 signatures are independently pinned in the owning repair
witness. These models require the reviewed public recipe and retain the actual
normal-UID, null-refusal, descriptor and post-removal assertions; they do not
execute Android or predict its MANAGE_EXTERNAL_STORAGE permission mapping.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "tests/consumer/android-storage-probe/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/verification/storageprobe"
LOOKUP = "checkNotNull(AppOpsManager.permissionToOp(Manifest.permission.MANAGE_EXTERNAL_STORAGE))"
OPT_IN = "@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)"


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def manager_surface(source, control=False):
    begin = "if (Build.VERSION.SDK_INT >= 30) {"
    end = '} else { status.put("manager", JSONObject.NULL)' if control else 'putBoolean("resumed"'
    require(begin in source and end in source, "Keep the original API30+ native manager boundary")
    block = source[source.index(begin):source.index(end, source.index(begin))]
    require("val managerOp = " + LOOKUP in block, "Exact public permission lookup must refuse null")
    require("OPSTR_MANAGE_EXTERNAL_STORAGE" not in source, "No unavailable SDK constant")
    require(block.count("AppOpsManager.permissionToOp(") == 1 and "?:" not in block,
            "No alias, numeric or fallback substitution for an unknown operation")
    require("Environment.isExternalStorageManager()" in block, "Native manager state must remain observed")
    native_call = "appops.unsafeCheckOpNoThrow(managerOp, Process.myUid(), context.packageName)" if control else "appops.unsafeCheckOpNoThrow(managerOp,\n                Process.myUid(), context.packageName)"
    require(native_call in block, "Manager mode must be the real ordinary helper UID/package operation")
    require(('put("manager_mode",' if control else 'putInt("managerMode",') in block,
            "Keep the actual manager-mode observation field")


def native_file_cleanup(source):
    begin = "private fun probeOwnedFile("
    end = "private fun preserveCleanup("
    require(begin in source and end in source, "Keep the owned raw-file operation")
    block = source[source.index(begin):source.index(end, source.index(begin))]
    for token in (
        "OsConstants.O_RDWR or OsConstants.O_CREAT or OsConstants.O_EXCL",
        "check(Os.read(descriptor, ByteArray(1), 0, 1) == 0)",
        "check(actual.contentEquals(payload))",
        "Os.close(descriptor); check(!descriptor.valid()); closed = true",
        "if (!denialAllowed || created || failure.errno !in setOf(OsConstants.EACCES, OsConstants.EPERM))",
        "preserveCleanup(primary) {\n                if (created) {\n                    Os.remove(file.absolutePath)",
        'try { Os.lstat(file.absolutePath); error("Owned file still exists after unlink") }',
        "catch (failure: ErrnoException) { check(failure.errno == OsConstants.ENOENT) }",
        'response.putBoolean(prefix + ".cleanup", true)',
    ):
        require(token in block, "Throwing native cleanup/data/descriptor/denial invariant removed: " + token)
    require(block.count("Os.remove(file.absolutePath)") == 1 and "Os.unlink(" not in block,
            "Use the single public throwing native file removal, not hidden unlink")
    require("file.delete(" not in block and "deleteRecursively(" not in block,
            "Do not replace native throwing removal with an ignored Boolean deletion")


def control_opt_in_and_cleanup(source):
    require(source.startswith("// SPDX-License-Identifier: Apache-2.0\n" + OPT_IN + "\n\npackage "),
            "Use the existing explicit file opt-in for the experimental permission type")
    for token in (
        "check(Binder.getCallingUid() == 2000)",
        'context.enforceCallingPermission("android.permission.DUMP",',
        "StorageSession.current?.writeState = null",
        "check(removed.await(10, TimeUnit.SECONDS))",
        "check(StorageProbeActivity.active == null)",
        "check(context.contentResolver.persistedUriPermissions.isEmpty())",
        "StorageControlRecord.clear(context, nonce)",
        "Binder.restoreCallingIdentity(token)",
    ):
        require(token in source, "Opt-in must not bypass/remove owned cleanup or normal-UID admission: " + token)


class StorageSdkSurfaceGuards(unittest.TestCase):
    def test_session_manager_mode_uses_exact_public_nullable_permission_lookup(self):
        source = (HELPER / "StorageProbe.kt").read_text()
        manager_surface(source)
        for name, mutant in (
            ("hidden_constant", source.replace(LOOKUP, "AppOpsManager.OPSTR_MANAGE_EXTERNAL_STORAGE")),
            ("guessed_alias_on_null", source.replace(LOOKUP, 'AppOpsManager.permissionToOp(Manifest.permission.MANAGE_EXTERNAL_STORAGE) ?: "android:manage_external_storage"')),
            ("wrong_api_boundary", source.replace("Build.VERSION.SDK_INT >= 30", "Build.VERSION.SDK_INT >= 31")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                manager_surface(mutant)

    def test_control_manager_mode_keeps_native_uid_package_and_null_refusal(self):
        source = (HELPER / "StorageProbeControlProvider.kt").read_text()
        manager_surface(source, control=True)
        for name, mutant in (
            ("hidden_constant", source.replace(LOOKUP, "AppOpsManager.OPSTR_MANAGE_EXTERNAL_STORAGE")),
            ("guessed_alias_on_null", source.replace(LOOKUP, 'AppOpsManager.permissionToOp(Manifest.permission.MANAGE_EXTERNAL_STORAGE) ?: "android:manage_external_storage"')),
            ("wrong_native_uid", source.replace("unsafeCheckOpNoThrow(managerOp, Process.myUid()", "unsafeCheckOpNoThrow(managerOp, 2000")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                manager_surface(mutant, control=True)

    def test_public_native_remove_retains_descriptor_enoent_and_strict_denial(self):
        source = (HELPER / "StorageProbe.kt").read_text()
        native_file_cleanup(source)
        for name, mutant in (
            ("hidden_unlink", source.replace("Os.remove(file.absolutePath)", "Os.unlink(file.absolutePath)")),
            ("ignored_boolean_delete", source.replace("Os.remove(file.absolutePath)", "file.delete()")),
            ("missing_descriptor_invalidation", source.replace("check(!descriptor.valid()); ", "")),
            ("unknown_post_removal_errno", source.replace("failure.errno == OsConstants.ENOENT", "failure.errno >= 0")),
            ("post_creation_denial_laundered", source.replace("!denialAllowed || created || ", "!denialAllowed || ")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                native_file_cleanup(mutant)

    def test_control_file_opt_in_preserves_permission_cleanup_and_shell_boundary(self):
        source = (HELPER / "StorageProbeControlProvider.kt").read_text()
        control_opt_in_and_cleanup(source)
        for name, mutant in (
            ("missing_explicit_opt_in", source.replace(OPT_IN + "\n\n", "")),
            ("missing_permission_state_cleanup", source.replace("StorageSession.current?.writeState = null", "")),
            ("arbitrary_caller_uid", source.replace("Binder.getCallingUid() == 2000", "Binder.getCallingUid() >= 0")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                control_opt_in_and_cleanup(mutant)


CORE = ROOT / 'calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions'
ASSERTION_RECIPES = {'AndroidPermissionDemoDeviceTest.kt': ['for (name in OwnedPermissionDemo.FORBIDDEN) assertNotContains(declared, "android.permission.$name")', 'for (name in OwnedPermissionDemo.FORBIDDEN) assertFalse("android.permission.$name" in declared,\n            "Forbidden permission android.permission.$name is declared: $declared")'], 'OwnedPermissionDemo.kt': ['for (permission in FORBIDDEN) assertNotContains(declarations, "android.permission.$permission")', 'for (permission in FORBIDDEN) assertFalse("android.permission.$permission" in declarations,\n            "Forbidden permission android.permission.$permission is declared: $declarations")']}
ROOT_VALUES = 'val values = mapOf(Root.COLUMN_ROOT_ID to "storage-root", Root.COLUMN_DOCUMENT_ID to "root",\n                Root.COLUMN_TITLE to "NativeCmpKit storage test", Root.COLUMN_FLAGS to 0,\n                Root.COLUMN_MIME_TYPES to "application/octet-stream")'
DOCUMENT_VALUES = 'val values = mapOf(Document.COLUMN_DOCUMENT_ID to id,\n            Document.COLUMN_DISPLAY_NAME to if (isRoot) "NativeCmpKit storage test" else id,\n            Document.COLUMN_MIME_TYPE to if (isRoot) Document.MIME_TYPE_DIR else "application/octet-stream",\n            Document.COLUMN_FLAGS to 0, Document.COLUMN_SIZE to (file?.length() ?: 0),\n            Document.COLUMN_LAST_MODIFIED to (file?.lastModified() ?: 0))'
ROOT_COLUMNS = 'val columns = projection ?: arrayOf(Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID,\n            Root.COLUMN_TITLE, Root.COLUMN_FLAGS, Root.COLUMN_MIME_TYPES)'
DOCUMENT_COLUMNS = 'val columns = projection ?: arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,\n            Document.COLUMN_MIME_TYPE, Document.COLUMN_FLAGS, Document.COLUMN_SIZE, Document.COLUMN_LAST_MODIFIED)'


def forbidden_permission_membership(source, owned=False):
    filename = "OwnedPermissionDemo.kt" if owned else "AndroidPermissionDemoDeviceTest.kt"
    before, after = ASSERTION_RECIPES[filename]
    require(after in source and before not in source and "assertNotContains(" not in source,
            "Use equivalent false membership with the offending declaration diagnostic")
    require('.getStringArray("declaredPermissions")).toSet()' in source,
            "Keep the required nonnull native declaration collection")
    if owned:
        require('val FORBIDDEN = listOf("MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS")' in source,
                "Do not omit any forbidden permission")
        require('assertContains(declarations, "android.permission.$permission")' in source,
                "Keep the required Call/media declarations")
    else:
        require('consumer.request("file-picker")' in source and 'consumer.request("image-picker")' in source,
                "Keep both real picker scenarios")


def typed_projection_rows(source, root=False):
    values, columns = (ROOT_VALUES, ROOT_COLUMNS) if root else (DOCUMENT_VALUES, DOCUMENT_COLUMNS)
    conversion = "addRow(columns.map(values::get).toTypedArray<Any?>())" if root else "addRow(columnNames.map(values::get).toTypedArray<Any?>())"
    require(values in source, "Preserve every heterogeneous native value and expression")
    require(columns in source, "Preserve caller/default projection order")
    require(conversion in source, "Type only the actual owning row conversion as Any?")
    require('.filterNotNull()' not in source, "Keep unknown nullable projected columns and row shape")


class ReporterCompilerSurfaceGuards(unittest.TestCase):
    def test_picker_forbidden_permissions_keep_false_membership_and_diagnostic(self):
        source = (CORE / "AndroidPermissionDemoDeviceTest.kt").read_text()
        forbidden_permission_membership(source)
        before, after = ASSERTION_RECIPES["AndroidPermissionDemoDeviceTest.kt"]
        for name, mutant in (
            ("missing_kotlin_assertion", source.replace(after, before)),
            ("wrong_assertion_polarity", source.replace(after, after.replace("assertFalse(", "assertTrue("))),
            ("forbidden_list_bypassed", source.replace("for (name in OwnedPermissionDemo.FORBIDDEN)", "for (name in emptyList<String>())")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                forbidden_permission_membership(mutant)

    def test_owned_admission_keeps_every_forbidden_and_required_permission(self):
        source = (CORE / "OwnedPermissionDemo.kt").read_text()
        forbidden_permission_membership(source, owned=True)
        before, after = ASSERTION_RECIPES["OwnedPermissionDemo.kt"]
        for name, mutant in (
            ("missing_kotlin_assertion", source.replace(after, before)),
            ("wrong_assertion_polarity", source.replace(after, after.replace("assertFalse(", "assertTrue("))),
            ("forbidden_sms_omission", source.replace(', "RECEIVE_SMS"', "")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                forbidden_permission_membership(mutant, owned=True)

    def test_root_projection_array_types_any_without_changing_values(self):
        source = (CORE / "StorageTestDocumentsProvider.kt").read_text()
        typed_projection_rows(source, root=True)
        for name, mutant in (
            ("intersection_reified_again", source.replace("columns.map(values::get).toTypedArray<Any?>()", "columns.map(values::get).toTypedArray()")),
            ("unknown_projection_null_removed", source.replace("columns.map(values::get).toTypedArray<Any?>()", "columns.map(values::get).filterNotNull().toTypedArray<Any?>()")),
            ("root_flag_value_changed", source.replace("Root.COLUMN_FLAGS to 0", "Root.COLUMN_FLAGS to 1")),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                typed_projection_rows(mutant, root=True)

    def test_document_projection_array_keeps_all_native_types_and_expressions(self):
        source = (CORE / "StorageTestDocumentsProvider.kt").read_text()
        typed_projection_rows(source)
        for name, mutant in (
            ("intersection_reified_again", source.replace("columnNames.map(values::get).toTypedArray<Any?>()", "columnNames.map(values::get).toTypedArray()")),
            ("unknown_projection_null_removed", source.replace("columnNames.map(values::get).toTypedArray<Any?>()", "columnNames.map(values::get).filterNotNull().toTypedArray<Any?>()")),
            ("native_size_type_changed", source.replace("(file?.length() ?: 0)", '(file?.length()?.toString() ?: "0")')),
        ):
            with self.subTest(refused=name), self.assertRaises(AssertionError):
                typed_projection_rows(mutant)


if __name__ == "__main__":
    unittest.main()
