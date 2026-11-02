"""Passive source admission for the two named local-system-provider methods.

This does not install/acquire a provider, seed storage, grant access or certify
native behavior. Only the existing exclusive API35 emulator controller may
supply execution evidence. Cloud coverage is deliberately absent.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from android_io_named_system_documents_gate_observations import (
    gate_observation_preimage, gate_observation_postimage, gate_observation_present,
)
from android_io_named_button_rendering import rendering_present

FOCUS = "android-io-named-system-providers"
CLASS = "com.mohamedrejeb.calf.io.AndroidIoNamedSystemProviderTest"
KOTLIN = "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/"
TEST = KOTLIN + "AndroidIoNamedSystemProviderTest.kt"
CALLER = KOTLIN + "AndroidIoSystemTreeGrantActivity.kt"
UI = KOTLIN + "NamedSystemDocumentsUi.kt"
DESCRIPTOR = KOTLIN + "DeviceDescriptorProbe.kt"
MANIFEST = "calf-io/src/androidDeviceTest/AndroidManifest.xml"
SOURCE_FILES = (TEST, CALLER, UI, DESCRIPTOR, MANIFEST)
METHODS = (
    "externalStorageProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership",
    "downloadsProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership",
)
ANDROID = "{http://schemas.android.com/apk/res/android}"

# Exact owning resource helpers only; native selectors/lifecycle stay separate.
_RESOURCE_REFUSAL_SOURCE = r'''    private fun resource(id: String): String {
        // The R namespace need not be the package name of a Google-repackaged system application.
        val namespace = "com.android.documentsui"
        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
        val value = resources.getIdentifier(id, "id", namespace)
        check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {
            resourceRefusal("The exact stock DocumentsUI control resource is unavailable",
                resources, value, "id/$id")
        }
        return resources.getResourceName(value)
    }

    private fun stringResource(name: String, vararg arguments: Any): String {
        val namespace = "com.android.documentsui"
        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
        val value = resources.getIdentifier(name, "string", namespace)
        check(value != 0 && resources.getResourceName(value) == "$namespace:string/$name") {
            resourceRefusal("The exact stock DocumentsUI string resource is unavailable",
                resources, value, "string/$name")
        }
        return resources.getString(value, *arguments).also { check(it.isNotBlank() && it.length <= 1024) }
    }

    // Failure-only metadata observations never select or authorize a replacement resource.
    private fun resourceRefusal(message: String, resources: android.content.res.Resources,
        value: Int, requested: String): String {
        val application = when (packageName) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            else -> "OTHER_REFUSED"
        }
        val request = when (requested) {
            "id/dir_list" -> "DIR_LIST"
            "id/toolbar" -> "TOOLBAR"
            "string/open_tree_button" -> "OPEN_TREE_BUTTON"
            "string/open_tree_dialog_title" -> "OPEN_TREE_DIALOG_TITLE"
            "string/open_tree_dialog_message" -> "OPEN_TREE_DIALOG_MESSAGE"
            "string/allow" -> "ALLOW"
            else -> "OTHER_REFUSED"
        }
        // Only the original check's lazy false branch calls this function.
        // Nonzero means its exact-name comparison completed false, not a new lookup.
        val nonzero = value != 0
        val nameMatchFromRefusal: Boolean? = if (nonzero) false else null
        val label = admittedLabelResource
        return "$message;documentsUiResourceRefusalSchema=1,request=$request,application=$application," +
            "canonicalIdentifierNonzero=$nonzero,canonicalNameMatchFromRefusal=$nameMatchFromRefusal," +
            "canonicalPostRefusalNamespace=${resourceNamespaceCategory(resources, value)}," +
            "applicationLabelIdentifierNonzero=${label?.let { it != 0 }}," +
            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}" +
            "," + fixedCandidateResourceQualification(resources, requested)
    }

    private fun resourceNamespaceCategory(resources: android.content.res.Resources, value: Int): String {
        if (value == 0) return "ZERO_IDENTIFIER"
        // Additional post-refusal readback only. A label resource is not whole-table ownership.
        // Neither a resource name nor a diagnostic exception may escape into the failure report.
        return try {
            val name = resources.getResourceName(value)
            when {
                name.startsWith("com.android.documentsui:") -> "AOSP_DOCUMENTS_UI"
                name.startsWith("com.google.android.documentsui:") -> "GOOGLE_DOCUMENTS_UI"
                name.startsWith("android:") -> "ANDROID_FRAMEWORK"
                ':' in name -> "OTHER_NAMESPACE"
                else -> "UNAVAILABLE"
            }
        } catch (_: Throwable) {
            "UNAVAILABLE" // Preserve the original IllegalStateException and its fixed message prefix.
        }
    }

'''
_RESOURCE_QUALIFICATION_SOURCE = r'''    // A bounded failure-only candidate observation, never a control/namespace admission.
    private fun fixedCandidateResourceQualification(resources: android.content.res.Resources,
        requested: String): String = try {
        // Same Resources instance from the original canonical check; label observations are not authority.
        val eligible = requested == "id/dir_list" && packageName == "com.google.android.documentsui"
        val candidateNamespace = "com.google.android.documentsui"
        val contracts = arrayOf(
            Triple("DIR_LIST", "id", "dir_list"),
            Triple("TOOLBAR", "id", "toolbar"),
            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button"),
            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),
            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),
            Triple("ALLOW", "string", "allow"),
        )
        var identifierLookupCount = 0
        var nameReadbackCount = 0
        var identifierNonzeroCount = 0
        var exactFullNameCount = 0
        val facts = ArrayList<String>(6)
        for ((category, type, entry) in contracts) {
            val identifier: Int? = if (eligible) try {
                identifierLookupCount += 1
                resources.getIdentifier(entry, type, candidateNamespace)
            } catch (_: Throwable) {
                null
            } else null
            val nonzero: Boolean? = identifier?.let { it != 0 }
            if (nonzero == true) identifierNonzeroCount += 1
            val exactFullNameMatch: Boolean? = if (identifier != null && identifier != 0) try {
                nameReadbackCount += 1
                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"
            } catch (_: Throwable) {
                null
            } else null
            if (exactFullNameMatch == true) exactFullNameCount += 1
            facts += "candidate${category}IdentifierNonzero=$nonzero," +
                "candidate${category}ExactFullNameMatch=$exactFullNameMatch"
        }
        val scope = if (eligible) "GOOGLE_DIR_LIST_REFUSAL" else "NOT_REQUESTED"
        val namespaceCategory = if (eligible) "GOOGLE_PACKAGE_CANDIDATE" else "NOT_REQUESTED"
        "candidateQualificationSchema=1,candidateScope=$scope,candidateNamespace=$namespaceCategory," +
            "candidateContractCount=6,candidateIdentifierLookupCount=$identifierLookupCount," +
            "candidateNameReadbackCount=$nameReadbackCount,candidateIdentifierNonzeroCount=$identifierNonzeroCount," +
            "candidateExactFullNameCount=$exactFullNameCount," + facts.joinToString(",")
    } catch (_: Throwable) {
        // A diagnostic failure must not replace the original lazy-check IllegalStateException.
        "candidateQualificationSchema=1,candidateScope=UNAVAILABLE,candidateNamespace=NOT_REQUESTED," +
            "candidateContractCount=6,candidateIdentifierLookupCount=-1,candidateNameReadbackCount=-1," +
            "candidateIdentifierNonzeroCount=-1,candidateExactFullNameCount=-1"
    }

'''

_RESOURCE_LABEL_ADMISSION_SOURCE = r'''    init {
        check(packageName in AndroidIoSystemTreeGrantActivity.SYSTEM_DOCUMENTS_UI)
        val app = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0)
        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        admittedLabelResource = app.labelRes
        automation.serviceInfo = automation.serviceInfo.apply {
'''


# Original canonical diagnostics stay literal for exact historical reconstruction only.
_RESOURCE_ADMISSION_FIELDS_SOURCE = '    private data class ResourceContract(val resources: android.content.res.Resources, val namespace: String)\n    private var admittedResourceContract: ResourceContract? = null\n'
_RESOURCE_ADMISSION_INITIALIZER_SOURCE = '    init {\n        check(packageName in AndroidIoSystemTreeGrantActivity.SYSTEM_DOCUMENTS_UI)\n        val app = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0)\n        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)\n        automation.serviceInfo = automation.serviceInfo.apply {\n'
_RESOURCE_ADMISSION_SELECT_BEFORE = '    fun selectOwnedFolder(folder: String) {\n        check(folder.matches(Regex("NativeCmpKitIo55-[a-f0-9]{32}")))\n'
_RESOURCE_ADMISSION_SELECT_SOURCE = '    fun selectOwnedFolder(folder: String) {\n        check(folder.matches(Regex("NativeCmpKitIo55-[a-f0-9]{32}")))\n        // The caller has already assigned this constructed UI to its finally owner.\n        // Qualify the complete literal app contract before any accessibility query or click.\n        qualifyResourceContract()\n'
_RESOURCE_ADMISSION_SOURCE = '    private fun qualifyResourceContract() {\n        check(admittedResourceContract == null) { "DocumentsUI resource contract was already qualified" }\n        // Application identity chooses one complete contract; no label-derived namespace or fallback.\n        val namespace = when (packageName) {\n            "com.android.documentsui" -> "com.android.documentsui"\n            "com.google.android.documentsui" -> "com.google.android.documentsui"\n            else -> error("DocumentsUI resource application refused;application=OTHER_REFUSED")\n        }\n        val resources = try {\n            instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)\n        } catch (_: Throwable) {\n            error(resourceAdmissionRefusal("RESOURCE_TABLE", namespace, null, null))\n        }\n        // All six original154 candidate roles were nonzero/exact; every execution must requalify.\n        val contracts = arrayOf(\n            Triple("DIR_LIST", "id", "dir_list"),\n            Triple("TOOLBAR", "id", "toolbar"),\n            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button"),\n            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),\n            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),\n            Triple("ALLOW", "string", "allow"),\n        )\n        for ((request, type, entry) in contracts) {\n            readQualifiedResource(resources, namespace, request, type, entry)\n        }\n        // No partial contract, zero/wrong readback or per-role namespace hybrid can be published.\n        admittedResourceContract = ResourceContract(resources, namespace)\n    }\n\n    private fun resource(id: String): String = qualifiedResource("id", id).second\n\n    private fun stringResource(name: String, vararg arguments: Any): String {\n        val (value, _) = qualifiedResource("string", name)\n        val resources = checkNotNull(admittedResourceContract).resources\n        val text = try {\n            resources.getString(value, *arguments)\n        } catch (_: Throwable) {\n            error("Exact admitted DocumentsUI string unavailable;request=STRING_VALUE")\n        }\n        return text.also {\n            check(it.isNotBlank() && it.length <= 1024) { "Exact admitted DocumentsUI string value refused" }\n        }\n    }\n\n    private fun qualifiedResource(type: String, entry: String): Pair<Int, String> {\n        val contract = checkNotNull(admittedResourceContract) { "DocumentsUI resource contract is unqualified" }\n        val request = when ("$type/$entry") {\n            "id/dir_list" -> "DIR_LIST"\n            "id/toolbar" -> "TOOLBAR"\n            "string/open_tree_button" -> "OPEN_TREE_BUTTON"\n            "string/open_tree_dialog_title" -> "OPEN_TREE_DIALOG_TITLE"\n            "string/open_tree_dialog_message" -> "OPEN_TREE_DIALOG_MESSAGE"\n            "string/allow" -> "ALLOW"\n            else -> error("DocumentsUI resource role refused;request=OTHER_REFUSED")\n        }\n        // Recheck consumed IDs/strings against the same fully qualified Resources object.\n        return readQualifiedResource(contract.resources, contract.namespace, request, type, entry)\n    }\n\n    private fun readQualifiedResource(resources: android.content.res.Resources, namespace: String,\n        request: String, type: String, entry: String): Pair<Int, String> {\n        val value: Int? = try {\n            resources.getIdentifier(entry, type, namespace)\n        } catch (_: Throwable) {\n            null\n        }\n        val nonzero: Boolean? = value?.let { it != 0 }\n        val fullName: String? = if (nonzero == true) try {\n            resources.getResourceName(checkNotNull(value))\n        } catch (_: Throwable) {\n            null\n        } else null\n        val exactFullNameMatch: Boolean? = fullName?.let { it == "$namespace:$type/$entry" }\n        check(nonzero == true && exactFullNameMatch == true) {\n            resourceAdmissionRefusal(request, namespace, nonzero, exactFullNameMatch)\n        }\n        return checkNotNull(value) to checkNotNull(fullName)\n    }\n\n    private fun resourceAdmissionRefusal(request: String, namespace: String,\n        nonzero: Boolean?, exactFullNameMatch: Boolean?): String {\n        val application = when (packageName) {\n            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"\n            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"\n            else -> "OTHER_REFUSED"\n        }\n        val declaredNamespace = when (namespace) {\n            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"\n            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"\n            else -> "OTHER_REFUSED"\n        }\n        // Only fixed categories and nullable booleans leave a refusal, never raw IDs/names/bodies.\n        return "The exact application-specific DocumentsUI resource is unavailable;" +\n            "documentsUiResourceAdmissionSchema=1,request=$request,application=$application," +\n            "declaredNamespace=$declaredNamespace,identifierNonzero=$nonzero," +\n            "exactFullNameMatch=$exactFullNameMatch"\n    }\n\n'

RESOURCE_ADMISSION_DELTAS = (
    ("    private var admittedLabelResource: Int? = null\n", _RESOURCE_ADMISSION_FIELDS_SOURCE),
    (_RESOURCE_LABEL_ADMISSION_SOURCE, _RESOURCE_ADMISSION_INITIALIZER_SOURCE),
    (_RESOURCE_ADMISSION_SELECT_BEFORE, _RESOURCE_ADMISSION_SELECT_SOURCE),
    (_RESOURCE_REFUSAL_SOURCE + _RESOURCE_QUALIFICATION_SOURCE, _RESOURCE_ADMISSION_SOURCE),
)


def resource_admission_preimage(ui: str) -> str:
    """Require the complete new owning shape, then reconstruct old source obligations.

    This is passive source validation, never a resource lookup or runtime receipt.
    An old-only/partial/hybrid shape cannot reach source_contract acceptance.
    """
    # Direct historical fixture callers invert the diagnostic first; source_contract still requires it.
    if isinstance(ui, str) and gate_observation_present(ui):
        ui = gate_observation_preimage(ui)
    require(isinstance(ui, str) and
            all(ui.count(after) == 1 for before, after in RESOURCE_ADMISSION_DELTAS) and
            ui.count("qualifyResourceContract(") == 2 and
            ui.count("qualifiedResource(") == 3 and
            ui.count("readQualifiedResource(") == 3 and
            ui.count("admittedResourceContract") == 5 and
            ui.count("resources.getIdentifier(") == 1 and
            ui.count("resources.getResourceName(") == 1 and
            ui.count("resources.getString(") == 1 and
            ui.count("getResourcesForApplication(") == 1 and
            "admittedLabelResource" not in ui and "app.labelRes" not in ui,
            "Application-specific DocumentsUI resource admission changed")
    for before, after in reversed(RESOURCE_ADMISSION_DELTAS):
        ui = ui.replace(after, before, 1)
    return ui


def resource_admission_postimage(ui: str) -> str:
    """Historical-control text bridge only; this does not accept a root or return a receipt.

    Exact original canonical/helper fragments must be present. Modified legacy
    obligations refuse rather than get silently overwritten by the new helper.
    """
    require(isinstance(ui, str), "Refusal-only DocumentsUI resource observations changed")
    for before, after in RESOURCE_ADMISSION_DELTAS:
        require(ui.count(before) == 1, "Refusal-only DocumentsUI resource observations changed")
        ui = ui.replace(before, after, 1)
    return gate_observation_postimage(ui)



def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_contract(root: Path) -> dict:
    values = {}
    for relative in SOURCE_FILES:
        path = root / relative
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 512 * 1024,
                "Missing bounded regular named-system-provider source")
        values[relative] = path.read_bytes()
    text = {name: value.decode("utf-8") for name, value in values.items()}
    test, caller, live_ui = (text[name] for name in (TEST, CALLER, UI))
    # Admission is mandatory before old canonical/selector/cleanup obligations are reconstructed.
    # Bare historical malformed resource shapes retain their original refusal category.
    # A valid resource shape without the NEW diagnostic still cannot return a source receipt.
    if not gate_observation_present(live_ui):
        resource_admission_preimage(live_ui)
    observed_ui = gate_observation_preimage(live_ui)
    require(rendering_present(live_ui),
            "System UI ownership, exact controls, ambiguity refusal or flag restoration changed")
    ui = resource_admission_preimage(observed_ui)
    require(re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", test) == list(METHODS) and
            "class AndroidIoNamedSystemProviderTest" in test and
            test.count("= runBlocking(Dispatchers.IO)") == 2 and
            not re.search(r"@(?:(?:org\.junit\.)?Ignore|Disabled|IgnoredTest)\b", test),
            "Exactly the two enabled missing named-provider methods are required")
    require(all("package com.mohamedrejeb.calf.io" in value for value in (test, caller, ui)),
            "Named-provider sources must retain the public library package")
    require(all(value in test for value in (
        'assertEquals(35, Build.VERSION.SDK_INT)', 'assertNotEquals(Looper.getMainLooper(), Looper.myLooper())',
        'assertEquals("en", context.resources.configuration.locales[0].language)',
        'assertTrue(context.contentResolver.persistedUriPermissions.isEmpty()',
        '"com.android.externalstorage.ExternalStorageProvider"', '"com.android.providers.downloads.DownloadStorageProvider"',
        'check(tree.scheme == "content" && tree.authority == authority',
        'assertOwnedRoot(root, seed.folder)', 'heldRoot = root',
        'val child = KmpFile(onlyOwnedChild(tree, rootId, seed))',
        'MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)',
        'val folder = "NativeCmpKitIo55-" + UUID.randomUUID()',
        'put(MediaStore.MediaColumns.IS_PENDING, 1)',
        'row = uri', 'assertIdentity()', 'openOutputStream(uri, "w")',
        'contentResolver.delete(uri, identityWhere, identityArgs) == 1',
        'MediaStore.MediaColumns.OWNER_PACKAGE_NAME', 'MediaStore.MediaColumns.RELATIVE_PATH',
        'cursor.getLong(0) == id && cursor.getString(1) == context.packageName',
        'cursor.getString(2) == fileName && cursor.getString(3) == relativePath',
        'check(!it.moveToFirst()) { "The unique MediaStore relative path already exists" }',
        'assertContentEquals(bytes, actual)',
        'context.contentResolver.openFileDescriptor(child.uri, "r")', 'DeviceDescriptorIdentity.of(it)',
        'child.readByteArray(context, maxBytes = seed.bytes.size)',
        'child.readByteArray(context, maxBytes = seed.bytes.size - 1)',
        'child.source(context).use { source ->', 'openDeviceDescriptorsFor(identity) > 0',
        'source.readAtMostTo(buffer, seed.bytes.size.toLong() - buffer.size)',
        'source.readAtMostTo(tail, 1)', 'openDeviceDescriptorsFor(identity))',
        'root.createBookmark(context)', 'activeScenario.close(); scenario = null', 'root.releaseBookmark(context)',
        'assertFailsWith<SecurityException>', 'first.addSuppressed(failure)', 'seed.closeOwnedRow()',
        'A late named system-provider observation is refused',
    )), "Owned seeding, URI identity, bounded public read, release or cleanup source boundary changed")
    require(test.index('check(tree.scheme == "content" && tree.authority == authority') <
            test.index('assertOwnedRoot(root, seed.folder)') < test.index('heldRoot = root') <
            test.index('root.createBookmark(context)'),
            "Unexpected native result must be refused before owned metadata/persistence")
    require(test.index('row = uri') < test.index('openOutputStream(uri, "w")') and
            test.index('val uri = row ?: return') < test.index('assertIdentity() // Unknown/changed identity') <
            test.index('assertIdentity() // Fresh identity') < test.index('contentResolver.delete(uri, identityWhere, identityArgs)'),
            "Insert ownership and fresh conditional cleanup ordering changed")
    require(all(value in caller for value in (
        'Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)', 'DocumentsContract.EXTRA_INITIAL_URI',
        'check(intent.component == null && intent.`package` == null && intent.selector == null)',
        'activity.applicationInfo.uid != Process.myUid()', 'startActivityForResult(intent, REQUEST_CODE)',
        'check(requested && resultCount == 0 && resultCode == null)', 'result = data', 'resultCount = 1',
    )), "Acquisition must remain an implicit real system UI callback, not a helper or injected result")
    require(all(value in ui for value in (
        'root.refresh() && root.isVisibleToUser && root.packageName?.toString() == packageName',
        'check(selected.size <= 1)', 'check(acquired.size <= 64)', 'resources.getResourceName(value)',
        'textIn(root, resource("dir_list"), folder)',
        '}, enclosingContainer = resource("dir_list"))',
        'find(nodes, matches, click = true, enclosingContainer = enclosingContainer)',
        'check(candidate.refresh() && candidate.isVisibleToUser && candidate.packageName?.toString() == packageName)',
        'check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                        "An owned DocumentsUI row ascent must not reach dir_list or higher"\n                                    }',
        'check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                    "The refreshed DocumentsUI container is not an owned row action"\n                                }',
        'it.viewIdResourceName == "android:id/title" && it.text?.toString() == folder',
        'textIn(root, resource("toolbar"), folder)',
        'val pickLabel = stringResource("open_tree_button")',
        'it.text?.toString() == pickLabel && it.isEnabled && it.isClickable',
        'context.packageManager.getApplicationLabel(context.applicationInfo).toString()',
        'val dialogTitle = stringResource("open_tree_dialog_title", callerLabel, folder)',
        'val dialogMessage = stringResource("open_tree_dialog_message", callerLabel, folder)',
        'check(dialogTitle.contains(folder) && dialogTitle.contains(callerLabel) &&',
        'dialogMessage.contains(folder) && dialogMessage.contains(callerLabel))',
        'val allowLabel = stringResource("allow")',
        'if (hasExactText(root, dialogTitle) && hasExactText(root, dialogMessage))',
        'it.text?.toString() == allowLabel && it.isEnabled && it.isClickable',
        'resources.getIdentifier(name, "string", namespace)',
        'resources.getResourceName(value) == "$namespace:string/$name"',
        'resources.getString(value, *arguments)',
        'check(containers.size <= 64)', 'check(selectedContainers.size <= 1)',
        'selectedContainers.single().findAccessibilityNodeInfosByText(expected)',
        'finally { containers.forEach { it.recycle() } }',
        'check(texts.size <= 64)', 'check(exactTexts.size <= 1)', 'it.text?.toString() == expected',
        'return exactTexts.size == 1', 'finally { texts.forEach { it.recycle() } }',
        'candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK)', 'flags = originalFlags',
    )) and not any(value in ui for value in ('resource("dir_title")', 'resource("action_menu_select")')),
        "System UI ownership, exact controls, ambiguity refusal or flag restoration changed")
    require(ui.count(_RESOURCE_REFUSAL_SOURCE) == 1 and
            ui.count(_RESOURCE_QUALIFICATION_SOURCE) == 1 and
            ui.count(_RESOURCE_LABEL_ADMISSION_SOURCE) == 1 and
            ui.count("    private var admittedLabelResource: Int? = null\n") == 1 and
            ui.count("admittedLabelResource") == 3 and
            ui.count("app.labelRes") == 1 and
            ui.count("resources.getIdentifier(") == 3 and
            ui.count("resources.getResourceName(") == 5 and
            ui.count("resourceRefusal(") == 3 and
            ui.count("fixedCandidateResourceQualification(") == 2,
            "Refusal-only DocumentsUI resource observations changed")
    ui_action_order = (
        'candidate = checkNotNull(candidate.parent).also { parents += it }',
        'check(candidate.refresh() && candidate.isVisibleToUser && candidate.packageName?.toString() == packageName)',
        'check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                        "An owned DocumentsUI row ascent must not reach dir_list or higher"\n                                    }',
        'check(candidate.refresh() && candidate.isVisibleToUser && candidate.isEnabled && candidate.isClickable)',
        'check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                    "The refreshed DocumentsUI container is not an owned row action"\n                                }',
        'check(SystemClock.elapsedRealtime() < deadline) { "A late DocumentsUI action is refused" }',
        'check(candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK))',
    )
    require(all(value in ui for value in ui_action_order) and
            [ui.index(value) for value in ui_action_order] == sorted(ui.index(value) for value in ui_action_order),
            "System UI ownership, exact controls, ambiguity refusal or flag restoration changed")
    forbidden = (
        "grantUriPermission(", "takePersistableUriPermission(", "revokeUriPermission(",
        "adoptShellPermissionIdentity(", "grantRuntimePermission(", "executeShellCommand(",
        "setComponentEnabledSetting(", "deleteRecursively(", "deleteDocument(", "java.io.File", "setComponent(",
        "OwnedIoEndpoint", "AndroidIoProviderContract", "Instrumentation.ActivityMonitor", "assumeTrue(",
    )
    require(not any(value in test + caller + ui for value in forbidden),
            "No controlled provider, direct URI grant, broad storage privilege, injected acquisition or directory deletion")
    manifest = ET.fromstring(values[MANIFEST])
    activities = manifest.findall("application/activity")
    require(sum(item.get(ANDROID + "name") == CLASS.rsplit('.', 1)[0] + ".AndroidIoSystemTreeGrantActivity" and
                item.get(ANDROID + "exported") == "false" for item in activities) == 1,
            "One nonexported native system-tree caller is required")
    require(any(item.get(ANDROID + "authorities") ==
                "media;com.android.externalstorage.documents;com.android.providers.downloads.documents"
                for item in manifest.findall("queries/provider")),
            "Named system-provider visibility must not request a new storage permission")
    require(not any(item.get(ANDROID + "name") in {
        "android.permission.MANAGE_DOCUMENTS", "android.permission.MANAGE_EXTERNAL_STORAGE",
        "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_VIDEO", "android.permission.READ_MEDIA_AUDIO"}
        for item in manifest.findall("uses-permission")), "Named-provider fixture must not acquire a broad storage privilege")
    return {"schema_version": 1, "verification_api_level": 35, "minimum_seed_api": 29,
            "controlled_helper_needed": False, "cloud_provider_coverage": False, "native_success_inferred": False,
            "source_files": {name: hashlib.sha256(value).hexdigest() for name, value in values.items()}}


def validate_source_receipt(receipt: dict) -> None:
    require(isinstance(receipt, dict) and set(receipt) == {
        "schema_version", "verification_api_level", "minimum_seed_api", "controlled_helper_needed",
        "cloud_provider_coverage", "native_success_inferred", "source_files"}, "Invalid named-provider source receipt schema")
    require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1 and
            type(receipt["verification_api_level"]) is int and receipt["verification_api_level"] == 35 and
            type(receipt["minimum_seed_api"]) is int and receipt["minimum_seed_api"] == 29 and
            receipt["controlled_helper_needed"] is False and receipt["cloud_provider_coverage"] is False and
            receipt["native_success_inferred"] is False, "A source receipt cannot certify native/cloud/helper behavior")
    require(isinstance(receipt["source_files"], dict) and set(receipt["source_files"]) == set(SOURCE_FILES) and
            all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in receipt["source_files"].values()),
            "Named-provider source receipt must contain the exact bounded source identities")
