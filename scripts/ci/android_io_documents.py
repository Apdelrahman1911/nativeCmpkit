"""Exact disposable API35 IO source and failure-safe owned preparation.

Source/APK/signing identity refusals precede the finite reporter compile. Native
UIDs, grants, Binder death, provider descriptors and Coil results remain real test
assertions, never inferred from these helper/source receipts. No outputs cached.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from android_geo_probe import metadata_apk
from android_share_recipient import OwnedShareRecipient
import library_tests as lt

PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.iodocuments"
FIXTURE = "tests/consumer/android-io-documents"
PERMISSION = PACKAGE + ".CONTROL_IO"
REPORTER = "com.mohamedrejeb.calf.calfio.test"
KOTLIN = "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/"
JAVA = FIXTURE + "/src/main/java/" + PACKAGE.replace(".", "/") + "/"
JAVA_NAMES = ("IoControlService", "IoDocumentGrantActivity", "IoFixture",
              "IoProviderWitnessService", "IoSingleDocumentGrantActivity", "OwnedIoDocumentsProvider")
KOTLIN_NAMES = ("AndroidIoGrantActivity", "AndroidIoProviderContract", "AndroidIoProviderLifecycleTest",
               "AndroidIoUnavailableProviderTest",
               "AndroidIoReferenceRegressionTest", "AndroidIoSingleDocumentGrantActivity",
               "DeviceDescriptorProbe", "IoBookmarkClientService", "KmpFileDeviceTest", "OwnedIoEndpoint")
REFERENCE_PROVIDER = KOTLIN + "instrumentation/DeviceIoFileProvider.kt"
REFERENCE_PATHS = "calf-io/src/androidDeviceTest/res/xml/nativecmpkit_io_device_paths.xml"
SOURCE_FILES = tuple(sorted(("gradle/libs.versions.toml", "calf-io/build.gradle.kts",
    "calf-io/src/androidDeviceTest/AndroidManifest.xml", FIXTURE + "/build.gradle.kts",
    FIXTURE + "/settings.gradle.kts", FIXTURE + "/gradle.properties", FIXTURE + "/src/main/AndroidManifest.xml",
    REFERENCE_PROVIDER, REFERENCE_PATHS,
    *(JAVA + name + ".java" for name in JAVA_NAMES), *(KOTLIN + name + ".kt" for name in KOTLIN_NAMES))))
# Explicit installed SDK recipe, not a searched/guessed signer or tool fallback.
SIGNER_REVISION = "36.0.0"
MAX_HOST_BYTES = 1024**2
ANDROID = "{http://schemas.android.com/apk/res/android}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_manifest(payload: bytes, *, compiled: bool) -> dict:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Expected bounded owned manifest bytes")
    try:
        manifest = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    except ET.ParseError as error:
        raise ValueError("Owned IO manifest is not XML") from error
    require(manifest.tag == "manifest" and (manifest.get("package") == PACKAGE if compiled else manifest.get("package") in {None, PACKAGE}) and
            manifest.get(ANDROID + "sharedUserId") is None and manifest.get(ANDROID + "sharedUserMaxSdkVersion") is None,
            "Wrong owned IO manifest package or shared-UID bypass")
    require(all(node.tag in {"permission", "queries", "application", "uses-sdk"} for node in manifest) and
            (compiled or not manifest.findall("uses-sdk")), "Unexpected owned IO manifest declarations")
    queries = manifest.findall("queries")
    require(len(queries) == 1 and len(queries[0]) == 1 and queries[0][0].tag == "package" and
            queries[0][0].get(ANDROID + "name") == REPORTER, "Only the fixed reporter package is visible to the helper")
    require(not manifest.findall("uses-permission") and not manifest.findall("uses-permission-sdk-23"),
            "The helper must not acquire broad content or runtime permissions")
    permissions, applications = manifest.findall("permission"), manifest.findall("application")
    require(len(permissions) == len(applications) == 1, "Expected one signature permission and application")
    permission, app = permissions[0], applications[0]
    levels = {"signature", "0x00000002", "0x2", "2"} if compiled else {"signature"}
    require(permission.get(ANDROID + "name") == PERMISSION and permission.get(ANDROID + "protectionLevel") in levels,
            "Only the fixed signature-level control permission is permitted")
    require(app.get(ANDROID + "allowBackup") == "false" and app.get(ANDROID + "permission") is None and
            app.get(ANDROID + "process") is None and app.get(ANDROID + "enabled") in {None, "true"},
            "No helper-wide process/permission override, disabled app or backup")
    activities, services, providers = app.findall("activity"), app.findall("service"), app.findall("provider")
    require((len(activities), len(services), len(providers)) == (2, 2, 1) and
            all(node.tag in {"activity", "service", "provider"} for node in app) and
            all(node.get(ANDROID + "enabled") in {None, "true"} for node in app), "Unexpected or disabled helper components")
    def component_name(node):
        value = node.get(ANDROID + "name", "")
        return PACKAGE + value if value.startswith(".") else value
    require({component_name(activity) for activity in activities} ==
            {PACKAGE + ".IoDocumentGrantActivity", PACKAGE + ".IoSingleDocumentGrantActivity"},
            "Only the exact tree and ordinary-document owner Activities are permitted")
    for activity in activities:
        require(activity.get(ANDROID + "exported") == "true" and
                activity.get(ANDROID + "permission") == PERMISSION and
                activity.get(ANDROID + "process") is None and len(activity) == 0,
                "Every grant/revoke dispatch must remain explicit and signature-protected")
    expected_services = {PACKAGE + ".IoControlService": None,
                         PACKAGE + ".IoProviderWitnessService": ":nativecmpkit_io_provider"}
    require({component_name(service) for service in services} == set(expected_services), "Wrong helper services")
    for service in services:
        expected_process = expected_services[component_name(service)]
        actual_process = service.get(ANDROID + "process")
        legal_processes = {expected_process}
        if compiled and expected_process is not None:
            legal_processes.add(PACKAGE + expected_process)
        require(service.get(ANDROID + "exported") == "true" and
                service.get(ANDROID + "permission") == PERMISSION and actual_process in legal_processes and
                len(service) == 0, "Wrong helper service permission/process boundary")
    provider = providers[0]
    require(component_name(provider) == PACKAGE + ".OwnedIoDocumentsProvider" and
            provider.get(ANDROID + "authorities") == (PACKAGE + ".documents" if compiled else "${applicationId}.documents") and
            provider.get(ANDROID + "permission") == "android.permission.MANAGE_DOCUMENTS" and
            provider.get(ANDROID + "readPermission") is None and provider.get(ANDROID + "writePermission") is None and
            provider.get(ANDROID + "exported") == "true" and provider.get(ANDROID + "grantUriPermissions") == "true" and
            provider.get(ANDROID + "process") in ({":nativecmpkit_io_provider", PACKAGE + ":nativecmpkit_io_provider"} if compiled else {":nativecmpkit_io_provider"}) and
            len(provider) == 1 and provider[0].tag == "intent-filter" and len(provider[0]) == 1 and
            provider[0][0].tag == "action" and provider[0][0].get(ANDROID + "name") == "android.content.action.DOCUMENTS_PROVIDER",
            "Content must require actual Android grants, never control-signature access, extra routes or grant/path overrides")
    if compiled:
        sdk = manifest.findall("uses-sdk")
        require(len(sdk) == 1 and sdk[0].get(ANDROID + "minSdkVersion") == "23" and
                sdk[0].get(ANDROID + "targetSdkVersion") == "37" and
                sdk[0].get(ANDROID + "maxSdkVersion") is None and app.get(ANDROID + "debuggable") == "true",
                "Unexpected compiled helper SDK/debug variant")
    return {"content_requires_android_grant": True, "signature_control_only": True,
            "fixed_helper_components_verified": True, "manifest_sha256": hashlib.sha256(payload).hexdigest(),
            "compiled_manifest_inspected": compiled, "native_grant_UID_or_result_inferred": False}


def validate_source_receipt(contract: dict) -> None:
    require(isinstance(contract, dict) and set(contract) == {"source_policy_verified", "source_inputs", "source_inputs_sha256", "native_or_compile_success_inferred"} and
            contract.get("source_policy_verified") is True and
            contract.get("native_or_compile_success_inferred") is False, "Missing source-only IO policy witness")
    inputs = contract.get("source_inputs")
    require(isinstance(inputs, dict) and tuple(sorted(inputs)) == SOURCE_FILES and
            all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in inputs.values()) and
            contract.get("source_inputs_sha256") == lt.input_digest(inputs), "Unknown or changed IO source identity")


def validate_reference_sources(texts: dict[str, str]) -> None:
    """Source-only owning restrictions; never proof of a returned grant/read/PFD."""
    reference = texts[KOTLIN + "AndroidIoReferenceRegressionTest.kt"]
    caller = texts[KOTLIN + "AndroidIoSingleDocumentGrantActivity.kt"]
    owner = texts[JAVA + "IoSingleDocumentGrantActivity.java"]
    require(re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", reference) == list(lt.ANDROID_IO_REFERENCE_METHODS) and
            re.search(r"\bclass\s+AndroidIoReferenceRegressionTest\b", reference) is not None and
            re.search(r"(?m)^package\s+com\.mohamedrejeb\.calf\.io\s*$", reference) is not None and
            not re.search(r"@(Ignore|Disabled|IgnoredTest)\b", reference) and
            reference.count("= runBlocking(Dispatchers.IO)") == len(lt.ANDROID_IO_REFERENCE_METHODS),
            "Every exact native reference method must remain enabled and off the main Looper")
    require(all(token in reference for token in (
        'assertNull(uri.query,', 'OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE',
        'assertNull(reference.createBookmark(context),', 'assertNull(KmpFile.fromBookmark(uri.toString(), context))',
        'assertEquals(0, openDeviceDescriptorsFor(identity))', 'assertFailsWith<FileNotFoundException>',
        'assertTrue(directory.deleteRecursively()); assertFalse(directory.exists())',
        'first.addSuppressed(failure)', 'assertContentEquals(sentinel, sibling.readBytes())',
        'ownerTransaction(owner, revoke = true)', 'heldBookmark = assertNotNull(reference.createBookmark(context))',
        'assertEquals(read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION, result.flags and grantMask)',
        'assertUriPermission(AndroidIoProviderContract.tree, read, PackageManager.PERMISSION_DENIED)',
        'assertUriPermission(sibling, read, PackageManager.PERMISSION_DENIED)',
        'assertEquals(owner.getInt("uid"), actual.getIntExtra("uid", -1))',
        'assertEquals(owner.getString("generation"), actual.getStringExtra("generation"))')),
        "Reference metadata, real ownership, denial, bookmark or failure-safe cleanup source changed")
    transaction = reference.split("private suspend fun ownerTransaction", 1)
    require(len(transaction) == 2, "Missing genuine ordinary-document owner transaction")
    scoped = re.search(r"ActivityScenario\.launch\(AndroidIoSingleDocumentGrantActivity::class\.java\)\.use\s*\{\s*scenario\s*->(.*?)\n        \}\n        return assertNotNull\(result\)", transaction[1], re.S)
    require(scoped is not None and "onResult(actual)" in scoped[1] and
            "startActivityForResult(" in caller and "firstDraw && hasWindowFocus()" in caller and
            "resultCode = code" in caller and "resultCount = 1" in caller and
            "IoSingleDocumentGrantActivity" in caller,
            "Bookmark callback must remain inside the real foreground grant-owning Activity scope")
    flags = re.findall(r"result\.addFlags\(([^)\r\n]*)\);", owner)
    require(flags == ["Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION"] and
            'Uri document = DocumentsContract.buildDocumentUri(IoFixture.AUTHORITY, "bookmark.txt");' in owner and
            all(token in owner for token in (
                "getCallingPackage()", "checkSignatures", "IoFixture.requireReporter", 'nonce.matches("[a-f0-9]{32}")',
                "DocumentsContract.isDocumentUri(this, document)", "DocumentsContract.isTreeUri(document)",
                'result.setDataAndType(document, "text/plain");', "result.setClipData(ClipData.newRawUri(",
                "revokeUriPermission(document, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);",
                "setResult(code, result);", "finish();", 'result = new Intent().putExtra("protocolError",')) and
            not any(token in owner for token in ("getParcelableExtra", "getData()", "FLAG_GRANT_PREFIX_URI_PERMISSION")),
            "Only one fixed ordinary document may receive read/persistable result flags or actual owner revoke")


def validate_unavailable_sources(texts: dict[str, str]) -> None:
    """Finite missing-only source refusals; this is not native provider-absence or cleanup proof."""
    source = texts[KOTLIN + "AndroidIoUnavailableProviderTest.kt"]
    control = texts[JAVA + "IoControlService.java"]
    endpoint = texts[KOTLIN + "OwnedIoEndpoint.kt"]
    require(re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source) == [lt.ANDROID_IO_UNAVAILABLE_METHOD] and
            re.search(r"\bclass\s+AndroidIoUnavailableProviderTest\b", source) is not None and
            re.search(r"(?m)^package\s+com\.mohamedrejeb\.calf\.io\s*$", source) is not None and
            not re.search(r"@(Ignore|Disabled|IgnoredTest)\b", source) and
            source.count("= runBlocking(Dispatchers.IO)") == 1,
            "The exact missing unavailable-provider method must remain enabled and off the main Looper")
    require(all(token in source for token in (
        'assertEquals(35, Build.VERSION.SDK_INT); assertEquals(UserHandle.getUserHandleForUid(0), Process.myUserHandle())',
        'assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, context.packageManager.getComponentEnabledSetting(providerComponent))',
        'val providerStatsBefore = stats(control, CHILD_ID)',
        'assertEquals(providerStatsBefore.getInt("uid"), providerWitness.getInt("uid"))',
        'assertEquals(providerStatsBefore.getInt("pid"), providerWitness.getInt("pid"))',
        'assertEquals(providerStatsBefore.getString("generation"), providerWitness.getString("generation"))',
        'leaseToken = token; restored = false', 'control.unavailable("acquire-unavailable", token)',
        'boundWitness.dieAndObserveBinderDeath()', 'control.unavailable("restore-unavailable", token)',
        'restored = true; leaseToken = null', 'if (restored) cleanupAttempt { assertQuiescent(control); control.request("reset") }',
        'cleanupAttempt { control.close() }', 'first.addSuppressed(failure)',
        'val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == AndroidIoProviderContract.tree }',
        'assertTrue(persisted.isReadPermission); assertFalse(persisted.isWritePermission)',
        'assertUriPermission(reference.uri, read, PackageManager.PERMISSION_GRANTED)',
        'assertUriPermission(reference.uri, write, PackageManager.PERMISSION_DENIED)',
        'ActivityScenario.launch(AndroidIoGrantActivity::class.java).use { scenario ->',
        'scenario.onActivity { it.selectOwnedTree() }',
        'result.flags and grantMask', 'FLAG_GRANT_PREFIX_URI_PERMISSION',
        'bookmark = assertNotNull(KmpFile(AndroidIoProviderContract.tree).createBookmark(context))')),
        "Unavailable identity must come from pre-outage nested provider stats, with real grants and exact failure-safe restoration")
    begin = "// BEGIN OWNED UNAVAILABLE WINDOW:"
    end = "// END OWNED UNAVAILABLE WINDOW."
    require(source.count(begin) == source.count(end) == 1, "Missing exact unavailable-window source boundary")
    before, remainder = source.split(begin, 1)
    window, after = remainder.split(end, 1)
    require(before.index('val providerStatsBefore = stats(control, CHILD_ID)') <
            before.index('val providerWitness = boundWitness.connect()') <
            before.index('control.unavailable("acquire-unavailable", token)') <
            before.index('boundWitness.dieAndObserveBinderDeath()') and
            after.index('control.unavailable("restore-unavailable", token)') < after.index('val providerStatsAfter = stats(control, CHILD_ID)'),
            "Provider identity, owned disabled lease, acknowledged real death or restore-before-stats ordering changed")
    require(not any(token in window for token in (
        'request("stats"', 'request("reset"', 'request("revoke"', 'stats(', 'assertQuiescent(',
        'acquireContentProviderClient(', 'acquireUnstableContentProviderClient(', 'ParcelFileDescriptor', 'contentResolver.query(')) and
            window.count('assertOwnedAuthorityAbsent()') == 2 and
            all(token in window for token in (
                'assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context))',
                'assertNull(reference.getName(context)); assertNull(reference.getSize(context))',
                'assertQualifiedAbsence(child) { child.readByteArray(context);', 'val unexpected = child.source(context)',
                'unexpected.close()', 'assertStillGranted(bookmark, root, child)',
                'windowFailure = failure; throw failure', 'val first = windowFailure', 'first.addSuppressed(failure)')),
            "Unavailable window must retain actual false/null metadata, unchanged grants, strict public reads and no provider reacquisition")
    absence = source.split('private suspend fun assertQualifiedAbsence', 1)
    require(len(absence) == 2, "Missing source-qualified public absence assertion")
    absence_body = absence[1].split('private fun assertUriPermission', 1)[0]
    require('catch (failure: FileNotFoundException) { failure }' in absence_body and
            'assertEquals(FileNotFoundException::class.java, absent.javaClass)' in absence_body and
            'assertEquals("No content provider: ${reference.uri}", absent.message)' in absence_body and
            'assertNull(absent.cause,' in absence_body and
            'catch (failure: Throwable)' not in absence_body and 'SecurityException' not in absence_body,
            "Only the qualified Android15 null-provider FileNotFoundException may satisfy public read/source absence")
    require(all(token in control for token in (
        'new ComponentName(IoFixture.PACKAGE,', 'IoFixture.PACKAGE + ".OwnedIoDocumentsProvider"',
        'IoFixture.requireReporter(this, message.sendingUid)', 'Process.myUserHandle().equals(UserHandle.getUserHandleForUid(0))',
        'declared.applicationInfo.uid != Process.myUid()', 'PackageManager.MATCH_DISABLED_COMPONENTS',
        'getPackageManager().resolveContentProvider(IoFixture.AUTHORITY, 0)',
        'resolved.applicationInfo.uid != Process.myUid()', 'token.matches("[a-f0-9]{32}")', 'request.size() != 3',
        'saved.size() != 2', 'token.equals(saved.get(LEASE_TOKEN))',
        'Integer.valueOf(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT).equals(saved.get(ORIGINAL_SETTING))',
        'setComponentEnabledSetting(OWNED_PROVIDER, PackageManager.COMPONENT_ENABLED_STATE_DISABLED,',
        'setComponentEnabledSetting(OWNED_PROVIDER, PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,',
        'PackageManager.DONT_KILL_APP', 'result.putInt("unavailableOriginalSetting", PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)',
        'result.putInt("unavailableActualSetting", actual)',
        'result.putBoolean("unavailableAuthorityPresent", !held)', 'result.putBoolean("unavailableLeaseHeld", held)')) and
            control.count('setComponentEnabledSetting(') == 2 and
            'COMPONENT_ENABLED_STATE_ENABLED' not in control and 'COMPONENT_ENABLED_STATE_DISABLED_USER' not in control,
            "Only the signature/nonce/UID/user0-authenticated fixed component and exact native DEFAULT lease may be mutated")
    acquire_parts = control.split('private void acquireUnavailable', 1)
    restore_parts = control.split('private void restoreUnavailable', 1)
    require(len(acquire_parts) == len(restore_parts) == 2, "Missing finite owned acquire/restore service methods")
    acquire = acquire_parts[1].split('private void restoreUnavailable', 1)[0]
    restore = restore_parts[1].split('private final Messenger endpoint', 1)[0]
    require(acquire.index('requireOwnedProvider(); requireNoUnavailableLease(); requireExactAuthority();') <
            acquire.index('.commit()') < acquire.index('requireMatchingLease(token);') < acquire.index('setComponentEnabledSetting(') and
            'getComponentEnabledSetting(OWNED_PROVIDER) != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT' in acquire and
            'leaseReceipt(result, token, true)' in acquire and
            'requireOwnedProvider(); requireMatchingLease(token);' in restore and
            'actual != PackageManager.COMPONENT_ENABLED_STATE_DISABLED && actual != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT' in restore and
            restore.index('setComponentEnabledSetting(') < restore.index('requireExactAuthority();') < restore.index('.clear().commit()') <
            restore.index('leaseReceipt(result, token, false)') and
            'getComponentEnabledSetting(OWNED_PROVIDER) != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT' in restore,
            "Fresh durable ownership must precede mutation; exact original setting/authority readback must precede clearing it")
    stats_block = control.split('else if ("stats".equals(operation)) {', 1)
    revoke_block = control.split('} else if ("revoke".equals(operation) || "reset".equals(operation)) {', 1)
    require(len(stats_block) == len(revoke_block) == 2 and
            stats_block[1].lstrip().startswith('requireNoUnavailableLease();') and
            revoke_block[1].lstrip().startswith('requireNoUnavailableLease();'),
            "Control stats/reset/revoke must refuse held or malformed unavailable leases before any provider/grant operation")
    require(all(token in endpoint for token in (
        'fun request(operation: String, id: String? = null): Bundle = transaction(operation, id)',
        'fun unavailable(operation: String, leaseToken: String): Bundle',
        'check(remoteOwner && component == ComponentName(AndroidIoProviderContract.PACKAGE,',
        '"${AndroidIoProviderContract.PACKAGE}.IoControlService") && processName == AndroidIoProviderContract.PACKAGE)',
        'check(operation in setOf("acquire-unavailable", "restore-unavailable"))',
        'transaction(operation, leaseToken = leaseToken)', 'putString("leaseToken", leaseToken)',
        'for (key in listOf("unavailableComponent", "unavailableAuthority", "unavailableLeaseToken"))',
        'for (key in listOf("unavailableOwnerUid", "unavailableUserId", "unavailableOriginalSetting", "unavailableActualSetting"))',
        'for (key in listOf("unavailableAuthorityPresent", "unavailableLeaseHeld"))',
        'assertIs<String>(data.get(key))', 'assertIs<Int>(data.get(key))', 'assertIs<Boolean>(data.get(key))',
        'data.containsKey(key)', 'assertEquals(owner.uid, data.getInt("unavailableOwnerUid"))',
        'assertEquals(AndroidIoProviderContract.AUTHORITY, data.getString("unavailableAuthority"))',
        'assertEquals(0, data.getInt("unavailableUserId"))',
        'assertEquals(leaseToken, data.getString("unavailableLeaseToken"))',
        'assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, data.getInt("unavailableOriginalSetting"))',
        'assertEquals(if (held) PackageManager.COMPONENT_ENABLED_STATE_DISABLED else PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,',
        'data.getInt("unavailableActualSetting"))',
        'assertEquals(!held, data.getBoolean("unavailableAuthorityPresent")); assertEquals(held, data.getBoolean("unavailableLeaseHeld"))')),
        "The exact control-only lease reply must retain nonce/native identity and mandatory typed setting/authority/ownership fields")
    require(not any(token in source + control for token in ('grantUriPermission(', 'Runtime.getRuntime', 'ProcessBuilder(',
            'acquireContentProviderClient(', 'acquireUnstableContentProviderClient(')),
            "No manual grant, shell state control or held provider-client substitution in unavailable-provider source")


def source_contract(root: Path) -> dict:
    texts, inputs = {}, {}
    for relative in SOURCE_FILES:
        path = lt.safe_path(root, relative); before = path.stat()
        require(path.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 256 * 1024,
                "Missing, linked or unbounded owned IO source")
        payload = path.read_bytes(); after = path.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), "IO source changed while reading")
        inputs[relative] = hashlib.sha256(payload).hexdigest(); texts[relative] = payload.decode("utf-8")
    actual = {path.relative_to(root).as_posix() for path in lt.source_files(root, FIXTURE + "/src")}
    require(actual == {FIXTURE + "/src/main/AndroidManifest.xml", *(JAVA + name + ".java" for name in JAVA_NAMES)},
            "Unexpected helper source inventory")
    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)
    reporter = ET.fromstring(texts["calf-io/src/androidDeviceTest/AndroidManifest.xml"],
                             parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    permissions = [node.get(ANDROID + "name") for node in reporter.findall("uses-permission")]
    applications, queries = reporter.findall("application"), reporter.findall("queries")
    require(reporter.tag == "manifest" and len(applications) == len(queries) == 1 and
            all(node.tag in {"uses-permission", "queries", "application"} for node in reporter) and
            not queries[0].attrib and len(queries[0]) in {1, 3} and
            queries[0][0].tag == "package" and queries[0][0].attrib == {ANDROID + "name": PACKAGE} and
            len(queries[0][0]) == 0 and
            (len(queries[0]) == 1 or (
                queries[0][1].tag == "provider" and queries[0][1].attrib == {ANDROID + "authorities":
                    "media;com.android.externalstorage.documents;com.android.providers.downloads.documents"} and
                len(queries[0][1]) == 0 and
                queries[0][2].tag == "intent" and not queries[0][2].attrib and len(queries[0][2]) == 1 and
                queries[0][2][0].tag == "action" and
                queries[0][2][0].attrib == {ANDROID + "name": "android.intent.action.OPEN_DOCUMENT_TREE"} and
                len(queries[0][2][0]) == 0)),
            "Only the exact helper query and reporter application are permitted")
    # The exact qualified named-system query pair and caller are an indivisible source-only union.
    named_system_union = len(queries[0]) == 3
    app = applications[0]
    require(permissions == [PERMISSION] and not reporter.findall("uses-permission-sdk-23") and
            reporter.get(ANDROID + "sharedUserId") is None and reporter.get(ANDROID + "sharedUserMaxSdkVersion") is None and
            app.get(ANDROID + "permission") is None and app.get(ANDROID + "process") is None,
            "Reporter must not bypass Android content grants or native UID/process boundaries")
    grant, client, providers = app.findall("activity"), app.findall("service"), app.findall("provider")
    require((len(grant), len(client), len(providers)) == (3 if named_system_union else 2, 1, 1) and
            all(node.tag in {"activity", "service", "provider"} for node in app) and
            all(node.get(ANDROID + "enabled") in {None, "true"} for node in app) and
            {activity.get(ANDROID + "name") for activity in grant} ==
                ({"com.mohamedrejeb.calf.io.AndroidIoGrantActivity", "com.mohamedrejeb.calf.io.AndroidIoSingleDocumentGrantActivity"} |
                 ({"com.mohamedrejeb.calf.io.AndroidIoSystemTreeGrantActivity"} if named_system_union else set())) and
            all(activity.get(ANDROID + "exported") == "false" and activity.get(ANDROID + "permission") is None and
                activity.get(ANDROID + "process") is None and len(activity) == 0 for activity in grant) and
            client[0].get(ANDROID + "name") == "com.mohamedrejeb.calf.io.IoBookmarkClientService" and
            client[0].get(ANDROID + "exported") == "false" and client[0].get(ANDROID + "process") == ":nativecmpkit_io_client" and
            client[0].get(ANDROID + "permission") is None and len(client[0]) == 0,
            "The exact reporter client and both grant/revoke Activities must remain private")
    if named_system_union:
        named_caller = next(activity for activity in grant if
                            activity.get(ANDROID + "name") == "com.mohamedrejeb.calf.io.AndroidIoSystemTreeGrantActivity")
        require(named_caller.attrib == {
                    ANDROID + "name": "com.mohamedrejeb.calf.io.AndroidIoSystemTreeGrantActivity",
                    ANDROID + "exported": "false", ANDROID + "theme": "@android:style/Theme.Material.Light.NoActionBar"} and
                len(named_caller) == 0,
                "Only the exact nonexported source-bound named-system caller is permitted")
    provider = providers[0]
    require(provider.get(ANDROID + "name") == "com.mohamedrejeb.calf.io.instrumentation.DeviceIoFileProvider" and
            provider.get(ANDROID + "authorities") == "${applicationId}.io-device-files" and
            provider.get(ANDROID + "exported") == "false" and provider.get(ANDROID + "grantUriPermissions") == "true" and
            provider.get(ANDROID + "process") == ":nativecmpkit_io_device_provider" and
            all(provider.get(ANDROID + name) is None for name in ("permission", "readPermission", "writePermission")) and
            len(provider) == 1 and provider[0].tag == "meta-data" and
            provider[0].get(ANDROID + "name") == "android.support.FILE_PROVIDER_PATHS" and
            provider[0].get(ANDROID + "resource") == "@xml/nativecmpkit_io_device_paths" and len(provider[0]) == 0,
            "Only the original private same-UID separate-process FileProvider with its fixed path resource is permitted")
    paths = ET.fromstring(texts[REFERENCE_PATHS], parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    require(paths.tag == "paths" and len(paths) == 1 and paths[0].tag == "cache-path" and
            paths[0].attrib == {"name": "io-device", "path": "nativecmpkit-io-device/"} and len(paths[0]) == 0,
            "Only the exact owned cache directory may be exposed by FileProvider")
    require('applicationId = "' + PACKAGE + '"' in texts[FIXTURE + "/build.gradle.kts"] and
            'namespace = "' + PACKAGE + '"' in texts[FIXTURE + "/build.gradle.kts"] and
            all(token in texts[FIXTURE + "/build.gradle.kts"] for token in (
                'compileSdk = libs.versions.android.compileSdk.get().toInt()',
                'minSdk = libs.versions.android.minSdk.get().toInt()',
                'targetSdk = libs.versions.android.compileSdk.get().toInt()',
                'sourceCompatibility = JavaVersion.VERSION_17', 'targetCompatibility = JavaVersion.VERSION_17')) and
            'from(files("../../../gradle/libs.versions.toml"))' in texts[FIXTURE + "/settings.gradle.kts"] and
            'implementation(projects.calfFilePickerCoil)' in texts['calf-io/build.gradle.kts'] and
            'implementation(libs.coil)' in texts['calf-io/build.gradle.kts'], "Unexpected helper/reporter build inputs")
    catalog = texts['gradle/libs.versions.toml']
    require('android-minSdk = "23"' in catalog and 'android-compileSdk = "37"' in catalog and 'coil = "3.6.2"' in catalog,
            "The exact source SDK/Coil declaration changed")
    for relative, required in {
        JAVA + "IoFixture.java": ("checkSignatures", "Build.VERSION.SDK_INT != 35", "getPackagesForUid"),
        JAVA + "IoControlService.java": ("message.sendingUid", 'nonce.matches("[a-f0-9]{32}")', "revokeUriPermission(IoFixture.tree()"),
        JAVA + "IoProviderWitnessService.java": ("message.sendingUid", "Process.killProcess(Process.myPid())", "delivered"),
        JAVA + "IoDocumentGrantActivity.java": ("getCallingPackage()", "checkSignatures", "FLAG_GRANT_PERSISTABLE_URI_PERMISSION", "FLAG_GRANT_PREFIX_URI_PERMISSION"),
        KOTLIN + "OwnedIoEndpoint.kt": ("message.sendingUid != owner.uid", "binder.linkToDeath", "death.await", "thread.quitSafely(); thread.join(10_000)", "check(pending.isEmpty())"),
        KOTLIN + "IoBookmarkClientService.kt": ("message.sendingUid == Process.myUid()", "getSharedPreferences", ".commit()", "Process.killProcess(Process.myPid())"),
        KOTLIN + "AndroidIoProviderLifecycleTest.kt": ("withImageLoader { loader ->", "withContext(NonCancellable)", "first.addSuppressed(failure)", "acquireUnstableContentProviderClient", "assertFailsWith<DeadObjectException>"),
    }.items():
        require(all(token in texts[relative] for token in required), "Owned nonce/UID/signature/service/cleanup source contract changed")
    lifecycle = texts[KOTLIN + "AndroidIoProviderLifecycleTest.kt"]
    require(re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", lifecycle) == list(lt.ANDROID_IO_PROVIDER_METHODS) and
            not re.search(r"@(Ignore|Disabled|IgnoredTest)\b", lifecycle), "Every new lifecycle method must remain authored and enabled")
    validate_reference_sources(texts)
    validate_unavailable_sources(texts)
    all_code = "\n".join(texts[JAVA + name + ".java"] for name in JAVA_NAMES) + "\n" + "\n".join(texts[KOTLIN + name + ".kt"] for name in KOTLIN_NAMES if name != "KmpFileDeviceTest") + "\n" + texts[REFERENCE_PROVIDER]
    require("grantUriPermission(" not in all_code and "Runtime.getRuntime" not in all_code and "acquireContentProviderClient(" not in texts[KOTLIN + "AndroidIoProviderLifecycleTest.kt"],
            "Manual grant, shell process or stable provider-death bypass is forbidden")
    contract = {"source_policy_verified": True, "source_inputs": inputs, "source_inputs_sha256": lt.input_digest(inputs),
                "native_or_compile_success_inferred": False}
    validate_source_receipt(contract)
    return contract


def signer_certificate(result: subprocess.CompletedProcess) -> str:
    require(isinstance(result.stdout, bytes) and isinstance(result.stderr, bytes) and
            len(result.stdout) + len(result.stderr) <= MAX_HOST_BYTES and result.returncode == 0 and not result.stderr.strip(),
            "APK signature verification unavailable")
    text = result.stdout.decode("utf-8")
    require(not re.search(r"(?im)\b(?:warning|error|does not verify)\b", text), "APK signer reported a warning or unverified detail")
    certificates = re.findall(r"(?m)^Signer #1 certificate SHA-256 digest: ([a-f0-9]{64})$", text)
    require(len(certificates) == 1 and re.search(r"(?m)^Number of signers: 1$", text) is not None and
            re.search(r"(?m)^Verified using v[23] scheme \([^\r\n]+\): true$", text) is not None and
            not re.search(r"(?m)^Signer #[2-9][0-9]* ", text), "Expected one verified actual APK signer")
    return certificates[0]


def validate_prepared_receipt(receipt: dict, expected_source: dict | None = None) -> None:
    require(isinstance(receipt, dict) and receipt.get("package") == PACKAGE and receipt.get("source_fixture") == FIXTURE and
            receipt.get("prepare_status") == "passed" and receipt.get("recipient_installed") is True and
            receipt.get("verification_api_level") == 35 and receipt.get("manual_URI_grant") is False and
            receipt.get("automatic_runtime_permission_grant") is False, "Owned IO helper preparation has not passed")
    digest = receipt.get("source_apk_sha256")
    installed, policy = receipt.get("installed_readback"), receipt.get("apk_policy")
    require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) and isinstance(installed, dict) and
            installed.get("apk_sha256") == digest and installed.get("exact_one_APK_path_observed") is True and
            isinstance(policy, dict) and policy.get("compiled_manifest_inspected") is True and
            policy.get("content_requires_android_grant") is True and policy.get("signature_control_only") is True and
            policy.get("certificate_sha256") == policy.get("private_key_certificate_sha256") and
            isinstance(policy.get("certificate_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", policy["certificate_sha256"]),
            "Owned helper APK, signing key or manifest identity disagrees")
    require(type(policy.get("signature_verification_min_sdk_version")) is int and
            policy["signature_verification_min_sdk_version"] == 35 and
            type(policy.get("signature_verification_max_sdk_version")) is int and
            policy["signature_verification_max_sdk_version"] == 35,
            "Owned helper signature verification must be explicitly API35-only")
    source = receipt.get("source_contract")
    validate_source_receipt(source)
    require(expected_source is None or source == expected_source, "Helper and reporter source plans differ")


class OwnedIoDocuments(OwnedShareRecipient):
    PACKAGE, FIXTURE, OUTPUT = PACKAGE, FIXTURE, "io-documents"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.receipt.update(verification_api_level=35,
            scope="Actual separate-UID DocumentsProvider with signature-only control. Exact tree read/persistable/prefix or ordinary-document read/persistable Activity-result grants remain native test assertions, as do owned client/provider restart, owner revocation and descriptor/Coil source-close checks. No real DocumentsUI/system/cloud provider, default decoder, memory/key benchmark, consumer/API-ABI or release certification.")

    def host(self, command: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(command, cwd=self.root, env=self.environment, capture_output=True, timeout=30)
        require(len(result.stdout) + len(result.stderr) <= MAX_HOST_BYTES, "Unbounded helper APK inspection")
        return result

    def inspectors(self) -> tuple[Path, Path]:
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        signer = self.home / ("build-tools/" + SIGNER_REVISION + "/apksigner")
        require(all(path.is_file() and os.access(path, os.X_OK) for path in (analyzer, signer)),
                "The explicit official APK inspector/signer recipe is unavailable")
        return analyzer, signer

    def inspect_apk(self, apk: Path) -> dict:
        analyzer, signer = self.inspectors()
        manifest = self.host([str(analyzer), "manifest", "print", str(apk)])
        require(manifest.returncode == 0 and not manifest.stderr.strip(), "Compiled helper manifest unavailable")
        policy = validate_manifest(manifest.stdout, compiled=True)
        # Only the authorized API35 runtime is checked; APK minSdk23 support is not inferred.
        certificate = signer_certificate(self.host([str(signer), "verify", "--verbose", "--print-certs",
            "--min-sdk-version", "35", "--max-sdk-version", "35", str(apk)]))
        key = Path(self.environment["ANDROID_USER_HOME"]) / "debug.keystore"
        checked = lt.safe_path(self.root, key.relative_to(self.root).as_posix())
        before = checked.stat()
        require(checked.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 65536,
                "The exact private controller debug key is unavailable")
        # Public default debug-key credentials only; never persist key bytes/paths/output.
        exported = self.host(["keytool", "-exportcert", "-keystore", str(checked), "-alias", "androiddebugkey", "-storepass", "android"])
        require(exported.returncode == 0 and not exported.stderr.strip() and 0 < len(exported.stdout) <= 16384,
                "The actual private debug-key certificate is unavailable")
        after = checked.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink),
                "The exact private debug-key input changed during certificate readback")
        expected = hashlib.sha256(exported.stdout).hexdigest()
        require(certificate == expected, "Helper was not signed by the controller's exact private key")
        return policy | {"certificate_sha256": certificate, "private_key_certificate_sha256": expected,
                         "apk_signer_revision": SIGNER_REVISION,
                         "signature_verification_min_sdk_version": 35, "signature_verification_max_sdk_version": 35,
                         "raw_manifest_certificate_key_or_paths_uploaded": False}

    def prepare(self):
        self.receipt["prepare_status"] = "running"
        try:
            self.receipt["source_contract"] = source_contract(self.root)
            self.inspectors()  # Reject a missing fixed SDK recipe before helper/reporter compilation.
            super().prepare()
            apk = metadata_apk(self.root, fixture=self.FIXTURE, package=self.PACKAGE)
            require(lt.sha256(apk) == self.digest, "Owned helper APK changed before policy inspection")
            self.receipt["apk_policy"] = self.inspect_apk(apk)
            require(lt.sha256(apk) == self.digest and source_contract(self.root) == self.receipt["source_contract"],
                    "Helper source or APK changed during preparation")
            self.receipt["prepare_status"] = "passed"
            validate_prepared_receipt(self.receipt)
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(prepare_status="failed", prepare_error=type(error).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def close(self):
        self.receipt["cleanup_status"] = "running"
        try:
            super().close()
            self.receipt["cleanup_status"] = "passed"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(cleanup_status="failed", cleanup_error=type(error).__name__, owned_recipient_removed=False)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)
