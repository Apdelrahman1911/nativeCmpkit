"""NEW controlled-loopback IO55 source helper: no production/API/native acceptance from guards.

The lead owns shared reporter-union, selector/workflow and always-finalizer wiring.
Only two NEW native identities (or a missing-only one-method follow-up) are legal.
Raw Socket's boundary is literal loopback/owned port/nonce, not NetworkSecurityConfig.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from android_geo_probe import unique
from android_io_documents import OwnedIoDocuments, SIGNER_REVISION, signer_certificate
import library_tests as lt

PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments"
AUTHORITY = PACKAGE + ".documents"
PERMISSION = PACKAGE + ".CONTROL_REMOTE_IO"
FIXTURE = "tests/consumer/android-io-remote-documents"
REPORTER = "com.mohamedrejeb.calf.calfio.test"
KOTLIN = "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/"
JAVA = FIXTURE + "/src/main/java/" + PACKAGE.replace(".", "/") + "/"
JAVA_NAMES = ("RemoteIoContract", "RemoteIoHttpBackend", "RemoteIoHttpTransport", "RemoteIoControlService",
              "RemoteIoDocumentsProvider", "RemoteIoProviderWitnessService")
KOTLIN_NAMES = ("AndroidIoRemoteDocumentsTest", "AndroidIoRemoteTreeGrantActivity", "RemoteIoEndpoint")
CLASS = "com.mohamedrejeb.calf.io.AndroidIoRemoteDocumentsTest"
METHODS = ("controlledRemoteTreeMetadataAndBoundedSourceCloseAreBackedByLiveHttp",
           "nativePendingRemoteOpenCancellationReleasesHttpSocketWithoutTransferringDescriptor")
FOCUSES = {"android-io-controlled-remote": METHODS,
           "android-io-controlled-remote-positive": METHODS[:1],
           "android-io-controlled-remote-cancel": METHODS[1:]}
ANDROID = "{http://schemas.android.com/apk/res/android}"
REPORTER_MANIFEST = "calf-io/src/androidDeviceTest/AndroidManifest.xml"
OLD_REPORTER_SHA256 = "397d45d9201637e6a696b3c4148376bb02fe5c4bb1070c541616bdcdaefeeb19"
# Exactly four reversible additions; neither the old reporter nor the accepted helper is generically repinned.
REPORTER_FRAGMENTS = (
    b'    <uses-permission android:name="io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments.CONTROL_REMOTE_IO" />\n',
    b'        <package android:name="io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments" />\n',
    b'        <provider android:authorities="io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments.documents" />\n',
    b'        <activity android:name="com.mohamedrejeb.calf.io.AndroidIoRemoteTreeGrantActivity" android:exported="false"\n'
    b'            android:theme="@android:style/Theme.Material.Light.NoActionBar" />\n',
)
REUSED_PINS = {
    KOTLIN + "NamedSystemDocumentsUi.kt": "e0251e1f3cc8bb4c93791b978d84de5bc4eb18469873c4879c190dbdd93956a0",
    KOTLIN + "DeviceDescriptorProbe.kt": "941c43e90bd8d32f113b3dc0b863b4885459a4f17716825eb26ffbf8b320a78a",
    KOTLIN + "AndroidIoSystemTreeGrantActivity.kt": "760634c61aa94ffb04b16f94fc20ceb67f4c58aa06477ee6dde14c3dda24fdde",
    KOTLIN + "OwnedIoEndpoint.kt": "c2180ba34f3c825e9060ddc68272b41c9d847f13cd91de7f7e2be54b496216a6",
}
SOURCE_FILES = tuple(sorted((REPORTER_MANIFEST, "calf-io/build.gradle.kts", "gradle/libs.versions.toml",
    FIXTURE + "/build.gradle.kts", FIXTURE + "/settings.gradle.kts", FIXTURE + "/gradle.properties",
    FIXTURE + "/src/main/AndroidManifest.xml", *(JAVA + name + ".java" for name in JAVA_NAMES),
    *(KOTLIN + name + ".kt" for name in KOTLIN_NAMES), *REUSED_PINS,
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt",
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileSource.android.kt",
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileBookmark.android.kt",
    "calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/BoundedRead.kt",
    "scripts/ci/android_geo_probe.py", "scripts/ci/android_io_documents.py", "scripts/ci/android_share_recipient.py", "scripts/ci/library_tests.py",
    "scripts/ci/android_io_remote_documents.py", "scripts/ci/test_android_io_remote_documents.py",
    "scripts/ci/android_device_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml",
    "scripts/ci/test_android_io_reporter_manifest_union.py",
    "scripts/ci/android_io_remote_routing_source_projection.py",
    "scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json",
    "scripts/ci/test_android_io_remote_routing_source_projection.py", "scripts/ci/test_android_io_remote_routing.py")))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def metadata_apk(root: Path, *, fixture: str = FIXTURE, package: str = PACKAGE) -> Path:
    """NEW exact-pair reader; do not broaden the accepted old helper's pair allowlist."""
    require((fixture, package) == (FIXTURE, PACKAGE), "Only the reviewed NEW remote fixture/package pair is permitted")
    base = lt.safe_path(root, fixture + "/build/outputs/apk/debug")
    path = lt.safe_path(root, (base / "output-metadata.json").relative_to(root).as_posix())
    require(path.is_file() and path.stat().st_nlink == 1 and 0 < path.stat().st_size <= 65536,
            "Actual bounded single remote APK metadata required")
    data = json.loads(path.read_bytes(), object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite remote APK metadata")))
    require(isinstance(data, dict) and data.get("applicationId") == package and data.get("variantName") == "debug" and
            isinstance(data.get("artifactType"), dict) and data["artifactType"].get("type") == "APK",
            "Foreign remote source APK metadata refused")
    rows = data.get("elements")
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "Exactly one remote APK metadata row required")
    row = rows[0]; name = row.get("outputFile")
    require(row.get("type") == "SINGLE" and row.get("filters") == [] and isinstance(name, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", name), "Only an unsplit owned remote APK, no traversal or extra variant")
    apk = lt.safe_path(root, (base / name).relative_to(root).as_posix())
    require(apk.is_file() and apk.stat().st_nlink == 1 and 0 < apk.stat().st_size < 256 * 1024**2,
            "Actual bounded regular remote APK required")
    return apk


def selected_methods(focus: str) -> tuple[str, ...]:
    require(type(focus) is str and focus in FOCUSES, "Only exact NEW remote or missing-only focus is allowed")
    return FOCUSES[focus]


def required_tests(focus: str) -> tuple[str, ...]:
    return tuple(CLASS + "." + method for method in selected_methods(focus))


def identities(focus: str) -> tuple[dict, ...]:
    return tuple({"classname": CLASS, "name": method} for method in selected_methods(focus))


def instrumentation_filter(focus: str) -> str:
    methods = selected_methods(focus)
    if focus == "android-io-controlled-remote":
        require(methods == METHODS, "Only the exact two NEW methods permit the class-only remote selector")
        return CLASS
    require(len(methods) == 1, "Only one exact missing remote method permits a class#method selector")
    return CLASS + "#" + methods[0]


def normalize_reporter_manifest(payload: bytes) -> bytes:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Bounded reporter bytes required")
    result = payload
    for fragment in REPORTER_FRAGMENTS:
        require(result.count(fragment) == 1, "Every exact remote reporter addition must occur once as a complete union")
        result = result.replace(fragment, b"", 1)
    require(hashlib.sha256(result).hexdigest() == OLD_REPORTER_SHA256,
            "Remote inverse must preserve the exact accepted old reporter bytes")
    return result


def validate_manifest(payload: bytes, *, compiled: bool) -> dict:
    require(type(compiled) is bool and isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Bounded remote manifest bytes required")
    try:
        manifest = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    except ET.ParseError as failure:
        raise ValueError("Remote helper manifest is not XML") from failure
    require(manifest.tag == "manifest" and manifest.get("package") in ({PACKAGE} if compiled else {None, PACKAGE}) and
            all(manifest.get(ANDROID + field) is None for field in ("sharedUserId", "sharedUserMaxSdkVersion")) and
            all(node.tag in {"uses-permission", "permission", "queries", "application", "uses-sdk"} for node in manifest),
            "Exact remote package without shared-UID/extra routes required")
    network = manifest.findall("uses-permission")
    require(len(network) == 1 and network[0].attrib == {ANDROID + "name": "android.permission.INTERNET"} and len(network[0]) == 0,
            "Only normal INTERNET is allowed in the NEW helper")
    permissions, queries, applications = manifest.findall("permission"), manifest.findall("queries"), manifest.findall("application")
    require(len(permissions) == len(queries) == len(applications) == 1, "One signature control/query/application required")
    levels = {"signature", "0x00000002", "0x2", "2"} if compiled else {"signature"}
    require(permissions[0].get(ANDROID + "name") == PERMISSION and permissions[0].get(ANDROID + "protectionLevel") in levels and
            len(permissions[0]) == 0 and len(queries[0]) == 1 and queries[0][0].tag == "package" and
            queries[0][0].attrib == {ANDROID + "name": REPORTER} and len(queries[0][0]) == 0,
            "Exact signature control and reporter visibility only")
    app = applications[0]
    require(app.get(ANDROID + "allowBackup") == "false" and
            all(app.get(ANDROID + field) is None for field in ("permission", "process", "networkSecurityConfig", "usesCleartextTraffic")) and
            app.get(ANDROID + "enabled") in {None, "true"}, "No app-wide bypass or fake Socket HTTP-policy claim")
    require(len(app) == 3 and len(app.findall("service")) == 2 and len(app.findall("provider")) == 1,
            "No helper grant Activity, aliases or extra components")
    def name(node):
        value = node.get(ANDROID + "name", "")
        return PACKAGE + value if value.startswith(".") else value
    services = {name(node): node for node in app.findall("service")}
    expected = {PACKAGE + ".RemoteIoControlService": None,
                PACKAGE + ".RemoteIoProviderWitnessService": ":nativecmpkit_io_remote_provider"}
    require(set(services) == set(expected), "Exact two control/witness services required")
    for component, process in expected.items():
        service = services[component]
        processes = {process, PACKAGE + process} if compiled and process is not None else {process}
        require(service.get(ANDROID + "exported") == "true" and service.get(ANDROID + "permission") == PERMISSION and
                service.get(ANDROID + "process") in processes and service.get(ANDROID + "enabled") in {None, "true"} and len(service) == 0,
                "Exact signature-service/process boundary required")
    provider = app.find("provider")
    processes = {":nativecmpkit_io_remote_provider", PACKAGE + ":nativecmpkit_io_remote_provider"} if compiled else {":nativecmpkit_io_remote_provider"}
    require(name(provider) == PACKAGE + ".RemoteIoDocumentsProvider" and provider.get(ANDROID + "authorities") ==
            (AUTHORITY if compiled else "${applicationId}.documents") and provider.get(ANDROID + "process") in processes and
            provider.get(ANDROID + "permission") == "android.permission.MANAGE_DOCUMENTS" and
            all(provider.get(ANDROID + field) is None for field in ("readPermission", "writePermission")) and
            provider.get(ANDROID + "exported") == provider.get(ANDROID + "grantUriPermissions") == "true" and
            provider.get(ANDROID + "enabled") in {None, "true"} and len(provider) == 1 and provider[0].tag == "intent-filter" and
            len(provider[0]) == 1 and provider[0][0].tag == "action" and provider[0][0].attrib ==
            {ANDROID + "name": "android.content.action.DOCUMENTS_PROVIDER"} and len(provider[0][0]) == 0,
            "Only standard MANAGE_DOCUMENTS/grant-capable provider, never signature content access or path grant bypass")
    sdk = manifest.findall("uses-sdk")
    if compiled:
        require(len(sdk) == 1 and sdk[0].get(ANDROID + "minSdkVersion") == "23" and
                sdk[0].get(ANDROID + "targetSdkVersion") == "37" and sdk[0].get(ANDROID + "maxSdkVersion") is None and
                app.get(ANDROID + "debuggable") == "true", "Exact compile37/min23 debug helper; native verification is API35 only")
    else:
        require(not sdk and app.get(ANDROID + "debuggable") is None, "Source SDK/debug variants belong only in the exact build recipe")
    return {"manifest_sha256": hashlib.sha256(payload).hexdigest(), "compiled_manifest_inspected": compiled,
            "content_requires_android_grant": True, "signature_control_only": True, "INTERNET_only": True,
            "no_helper_grant_activity": True, "native_or_consumer_success_inferred": False}


def contains(text: str, *tokens: str) -> bool:
    return all(token in text for token in tokens)


def validate_direct_native_population(test: str) -> None:
    """Narrow Kotlin source ownership only, not compilation or native discovery.

    A class-only selector is legal only for the exact two enabled direct methods.
    Mask comments/string/character literals before counting braces: an annotation
    in a nested class or quoted text cannot manufacture a direct test method.
    Original body-token validators below remain the owners of their refusals.
    """
    message = "Exactly two direct enabled noninherited NEW remote class methods required"
    require(type(test) is str and 0 < len(test.encode("utf-8")) <= 524288, message)
    cleaned = list(test)
    index = 0
    while index < len(test):
        start = index
        if test.startswith("//", index):
            end = test.find("\n", index + 2)
            index = len(test) if end < 0 else end
        elif test.startswith("/*", index):
            index += 2
            nesting = 1
            while index < len(test) and nesting:
                if test.startswith("/*", index):
                    nesting += 1; index += 2
                elif test.startswith("*/", index):
                    nesting -= 1; index += 2
                else:
                    index += 1
            require(nesting == 0, message)
        elif test.startswith('"""', index):
            end = test.find('"""', index + 3)
            require(end >= 0, message)
            index = end + 3
        elif test[index] in {'"', "'", "`"}:
            quote = test[index]; index += 1
            closed = False
            while index < len(test):
                if test[index] == "\\" and quote != "`":
                    index += 2
                elif test[index] == quote:
                    index += 1; closed = True; break
                else:
                    require(test[index] != "\n", message)
                    index += 1
            require(closed and index <= len(test), message)
        else:
            index += 1
            continue
        for position in range(start, index):
            if cleaned[position] != "\n":
                cleaned[position] = " "
    source = "".join(cleaned)
    require(re.findall(r"(?m)^package[ \t]+([^\n]+)$", source) == ["com.mohamedrejeb.calf.io"] and
            re.findall(r"(?m)^import[ \t]+(org\.junit\.[^\n]+)$", source) == ["org.junit.Test", "org.junit.runner.RunWith"] and
            re.findall(r"(?m)^import[ \t]+androidx\.test\.ext\.junit\.runners\.AndroidJUnit4[ \t]*$", source) ==
                ["import androidx.test.ext.junit.runners.AndroidJUnit4"] and
            not re.search(r"(?m)^import[^\n]+[ \t]as[ \t]|\btypealias\b", source) and
            not re.search(r"@(?:[A-Za-z_][A-Za-z0-9_]*\.)*(Ignore|Disabled|IgnoredTest)\b", source), message)
    owners = list(re.finditer(r"(?m)^@RunWith\(AndroidJUnit4::class\)\s+class AndroidIoRemoteDocumentsTest\s*\{", source))
    require(len(owners) == 1 and len(re.findall(r"\bclass\s+AndroidIoRemoteDocumentsTest\b", source)) == 1 and
            len(re.findall(r"@RunWith\b", source)) == 1, message)
    opening = owners[0].end() - 1
    depths, depth = [], 0
    for character in source:
        depths.append(depth)
        if character == "{": depth += 1
        elif character == "}": depth -= 1
        require(depth >= 0, message)
    require(depth == 0 and depths[opening] == 0, message)
    closing = next((position for position in range(opening + 1, len(source))
                    if source[position] == "}" and depths[position] == 1), None)
    require(closing is not None and not source[closing + 1:].strip(), message)
    annotations = list(re.finditer(r"@(?:[A-Za-z_][A-Za-z0-9_]*\.)*Test\b", source))
    declarations = list(re.finditer(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*=\s*runBlocking\(Dispatchers\.IO\)\s*\{", source))
    require(len(annotations) == len(declarations) == 2 and
            [node.start() for node in annotations] == [node.start() for node in declarations] and
            tuple(node.group(1) for node in declarations) == METHODS and
            all(opening < node.start() < closing and depths[node.start()] == 1 for node in declarations), message)


def validate_pump_writer_ownership(provider: str) -> None:
    """Lexical writer-order/cleanup guard only; never Java or reliable-pipe execution."""
    marker = "private static void pump(Transfer transfer, int first) {"
    require(provider.count(marker) == 1, "Exactly one owned remote pipe pump required")
    pump = provider.split(marker, 1)[1].split("    /** The only filesystem read", 1)[0]
    status = 'transfer.pipe[1].closeWithError("Owned remote producer failed")'
    require(not re.search(r"\btry\s*\(", pump) and pump.count("OutputStream output = null;") == 1 and
            pump.count("output = new ParcelFileDescriptor.AutoCloseOutputStream(transfer.pipe[1]);") == 1 and
            pump.count(status) == 1,
            "Handled reliable pipe producer error must precede any ordinary writer close without TWR")
    ordinary = re.search(r"(?:output|transfer\.pipe\[1\])\.close\(\)", pump)
    require(ordinary is not None and pump.index(status) < ordinary.start() and
            pump.index("OutputStream output = null;") < pump.index("output = new ParcelFileDescriptor.AutoCloseOutputStream"),
            "Handled reliable pipe producer error must precede any ordinary writer close without TWR")
    require(contains(pump, "primary = failure; transfer.failed(failure);",
            "if (failure != cleanup) failure.addSuppressed(cleanup);",
            "catch (Error failure) { primary = failure; throw failure; }",
            "if (output != null) output.close(); else transfer.pipe[1].close();",
            "if (primary == null) { primary = cleanup; transfer.failed(cleanup); }",
            "else if (primary != cleanup) primary.addSuppressed(cleanup);",
            "if (primary == cleanup && cleanup instanceof Error) throw (Error) cleanup;") and
            pump.count("catch (IOException | RuntimeException | Error cleanup)") == 2 and
            pump.count("synchronized (transfer.owner) { transfer.owner.cleanupErrors++; }") == 2 and
            len(re.findall(r"\bfinally\s*\{", pump)) == 2 and
            re.search(r"\}\s*finally\s*\{\s*transfer\.finish\(primary\);\s*\}\s*\}\s*\}", pump) is not None,
            "Reliable pipe writer cleanup must be independent, retain primary/suppressed errors and always finish")


def validate_sources(texts: dict[str, str]) -> None:
    test = texts[KOTLIN + "AndroidIoRemoteDocumentsTest.kt"]
    caller = texts[KOTLIN + "AndroidIoRemoteTreeGrantActivity.kt"]
    endpoint = texts[KOTLIN + "RemoteIoEndpoint.kt"]
    provider = texts[JAVA + "RemoteIoDocumentsProvider.java"]
    backend = texts[JAVA + "RemoteIoHttpBackend.java"]
    transport = texts[JAVA + "RemoteIoHttpTransport.java"]
    contract = texts[JAVA + "RemoteIoContract.java"]
    validate_direct_native_population(test)
    require(re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", test) == list(METHODS) and
            test.count("= runBlocking(Dispatchers.IO)") == 2 and "class AndroidIoRemoteDocumentsTest" in test and
            not re.search(r"@(Ignore|Disabled|IgnoredTest)\b", test), "Exactly two NEW enabled off-main native methods required")
    require(contains(caller, "Intent.ACTION_OPEN_DOCUMENT_TREE", "DocumentsContract.EXTRA_INITIAL_URI",
            "intent.component == null && intent.`package` == null && intent.selector == null", "resolved.exported",
            "FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP", "startActivityForResult(intent, REQUEST)",
            "result = data; resultCount = 1; resultCode = code"), "Only genuine implicit system tree/result UX is allowed")
    require(contains(test, 'check(DocumentsContract.getTreeDocumentId(tree) == RemoteIoContract.folder(session))',
            'tree.authority == RemoteIoContract.AUTHORITY && tree.query == null && tree.fragment == null',
            'val required = read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION',
            'result.clipData?.let { check(it.itemCount == 1 && it.getItemAt(0).uri == tree) }',
            'optionalWriteGrant = result.flags and write != 0', 'assertTrue(persisted.isReadPermission)',
            'assertNotNull(root.createBookmark(context))', 'KmpFile.fromBookmark(bookmark, context)',
            'assertNotNull(owner.caller).destroyed', 'owner.optionalWriteGrant, persisted.isWritePermission'),
            "Exact owned actual grants/bookmark restoration/optional native write must remain")
    require(contains(test, 'DeviceDescriptorIdentity.fromProvider(', 'The actual public source must own the newly transferred FIFO',
            'payload.source(context); owner.source = source', 'source.use {', 'RemoteIoContract.PAYLOAD_BYTES.toLong() - buffer.size',
            'assertEquals(owner.payloadHash, digest)', 'assertEquals(-1L, it.readAtMostTo(tail, 1)); assertEquals(0L, tail.size)',
            'EOF is not the caller\'s explicit FIFO close', 'assertEquals(0, openDeviceDescriptorsFor(assertNotNull(owner.identity)))',
            'assertSocketPair(transfer, server, owner.port)', 'provider.string("requestId"), backend.string("requestId")'),
            "Actual public bounded source/hash/EOF/explicit caller FIFO close/native socket pair assertions required")
    require(contains(test, 'context.contentResolver.openFileDescriptor(uri, "r", signal)',
            '"PENDING_FIRST_BODY" && transfer.bool("headersRead")', '!transfer.bool("pipeAllocated")',
            'server.bool("headersSent") && server.bool("heldWaiting") && server.int("bytesWritten") == 0',
            'pending.cancelFromVerifiedPending()', 'verifiedCancellationInvoked = true; signal.cancel()',
            'assertIs<OperationCanceledException>(failure)', 'assertNull(returned.get()',
            'assertEquals(1, transfer.int("cancellationAcknowledgments"))', 'assertTrue(transfer.bool("listenerClosedSocket"))',
            'assertFalse(server.bool("watchdogForced"))', 'assertFalse(assertNotNull(nativeThread).isAlive'),
            "Cancellation must follow native pending admission, actual signal and real failed native return/terminal")
    require(contains(transport, 'InetAddress.getByAddress(new byte[] {127, 0, 0, 1})', 'new Socket()',
            'new InetSocketAddress(loopback(), port)', 'owner.register(socket); registered = true;',
            'requireLoopback(socket, port, true)', 'socket.getLocalAddress()', 'socket.getInetAddress()',
            'RemoteIoContract.CONNECT_MS', 'RemoteIoContract.HELD_READ_MS : RemoteIoContract.READ_MS',
            'MAX_HEADER_LINES', 'MAX_HEADER_BYTES', 'lf != \'\\n\'', 'values.put(name, value) != null',
            'reply.keys("connection", "content-type", "content-length", "x-nativecmpkit-session"',
            '"HTTP/1.1 200 OK".equals(reply.first)', 'requestId.equals(reply.values.get("x-nativecmpkit-transfer"))',
            'input.read() != -1', 'sha256.equals(RemoteIoContract.sha256(bytes))'),
            "Strict native loopback/endpoints/HTTP finite header/schema/length/hash/EOF source guards required")
    require(contains(transport, 'deadline = System.nanoTime() + RemoteIoContract.READ_MS * 1_000_000L',
            'long remaining = deadline - System.nanoTime()', 'if (remaining <= 0) throw new SocketTimeoutException',
            'socket.setSoTimeout((int) Math.max(1, Math.min(RemoteIoContract.READ_MS,',
            'if (System.nanoTime() > deadline) throw new SocketTimeoutException',
            'socket.setSoTimeout(originalTimeout)', 'if (primary != null) primary.addSuppressed(cleanup); else throw cleanup;'),
            "Bounded HTTP aggregate header budget must resist per-byte timeout extension and preserve body timeout/primary failure")
    require(contains(contract, 'PAYLOAD_BYTES = 4097, HELD_BYTES = 131073', 'MAX_HEADER_BYTES = 8192, MAX_HEADER_LINES = 64',
            'MAX_METADATA_BYTES = 8192', 'MAX_JOURNAL = 128, MAX_CONNECTIONS = 4, ACCEPT_BACKLOG = 8',
            'CONNECT_MS = 2000, READ_MS = 5000, HELD_READ_MS = 15000', 'HELD_WATCHDOG_MS = 20000, JOIN_MS = 10000',
            'uid == Process.myUid()', 'packages.length != 1', 'checkSignatures', 'Build.VERSION.SDK_INT != 35',
            'request.keySet().equals(expected)'), "Finite bounds and separate-UID/authenticated typed native control required")
    require(contains(backend, 'new SecureRandom()', 'random.nextBytes(payload); random.nextBytes(held)',
            'listener = new ServerSocket()', 'setReuseAddress(false)', 'RemoteIoHttpTransport.loopback(), 0',
            'active.put(socket, connection); journal.add(connection)', 'connection.worker.start()',
            'RemoteIoContract.HELD_WATCHDOG_MS', 'connection.watchdogForced = true; errors++',
            'if (input.read() != -1)', 'connection.peerEof = true', 'listenerClosed', 'workerTerminal',
            'thread.join(RemoteIoContract.JOIN_MS)', 'Arrays.fill(payload, (byte) 0)', 'payload = null; held = null; dataCleared = true'),
            "Backend alone must own random bytes/listener, native peer EOF and joined bounded cleanup before data wipe")
    require(backend.index('thread.join(RemoteIoContract.JOIN_MS)') < backend.index('Arrays.fill(payload, (byte) 0)'),
            "Nonce data wipe must follow every attempted owned worker join")
    require(contains(provider, 'State owned = new State(session, token, port); state = owned;',
            'provision.open()', 'owned.rootDescriptor = fields', 'DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD',
            'DocumentsContract.Root.COLUMN_ICON, android.R.drawable.ic_menu_upload', 'notifyChange(DocumentsContract.buildRootsUri',
            'String body = owned.metadata("metadata", id)', 'String body = owned.metadata("children", id)',
            'transfer.phase = "PENDING_FIRST_BODY"', 'int first = exchange.input.read()',
            'transfer.pipe = ParcelFileDescriptor.createReliablePipe()', 'Os.fstat(transfer.pipe[0].getFileDescriptor())',
            'OsConstants.S_ISFIFO(stat.st_mode)', 'new FileInputStream("/proc/self/fdinfo/" + pipe.getFd())',
            'return transfer.pipe[0]', 'signal.setOnCancelListener(() ->', 'ownSocket.close()',
            'signal.throwIfCanceled()', 'cancelled.addSuppressed(failure)', 'operationCanceledObserved = true',
            'producerSocketEof = true', 'transfer.worker.start();', 'transfer.descriptorReturned = true;',
            'forcedCleanup = true; owner.errors++', 'owner.active.remove(requestId); done.countDown()'),
            "HTTP-provisioned cache only/live metadata/actual signal-before-pipe/FIFO/native EOF/terminal source required")
    opening = provider.split('Transfer transfer = owned.transfer("content", id, signal);', 1)[1].split('private static void pump', 1)[0]
    require(opening.index('transfer.phase = "PENDING_FIRST_BODY"') < opening.index('int first = exchange.input.read()') <
            opening.index('transfer.pipe = ParcelFileDescriptor.createReliablePipe()') < opening.index('return transfer.pipe[0]'),
            "Real held first socket byte must precede any native pipe allocation/return")
    require(re.search(r'synchronized \(owned\) \{\s+transfer\.worker\.start\(\);\s+'
            r'transfer\.descriptorReturned = true; owned\.descriptorReturns\+\+;\s+\}', opening) is not None,
            "Actual producer start/descriptor commit must share the owner lock so a fast worker cannot close an uncommitted read end")
    validate_pump_writer_ownership(provider)
    require(contains(endpoint, 'message.sendingUid != owner.uid', 'Parcel.obtain()', 'parcel.dataSize() <= 524288',
            'pending.remove(data.getString("nonce", ""))', 'thread.start()', 'checkSignatures',
            'binder.linkToDeath(deathRecipient, 0)', 'receipt.getInt("terminationSelfPid")', 'receipt.getBoolean("quiescentBeforeDeath")',
            'context.unbindService(connection)', 'death.await(15, TimeUnit.SECONDS)', 'assertFalse(binder.isBinderAlive',
            'thread.quitSafely(); thread.join(10_000); check(!thread.isAlive)', 'check(pending.isEmpty())'),
            "NEW typed UID/generation/nonce endpoint and acknowledged actual Binder death/thread join required")
    require(endpoint.index('// Remove BIND_AUTO_CREATE') < endpoint.index('death.await(15, TimeUnit.SECONDS)'),
            "Unbind owned self-kill endpoint before death wait to avoid implicit helper restart")
    for service_name, process in (("RemoteIoControlService", "RemoteIoContract.PACKAGE"),
                                  ("RemoteIoProviderWitnessService", "RemoteIoContract.PROVIDER_PROCESS")):
        service = texts[JAVA + service_name + ".java"]
        require(contains(service, 'RemoteIoContract.requireReporter(this, message.sendingUid, ' + process + ')',
                'RemoteIoContract.keys(request', 'new Handler(thread.getLooper(), this::receive)',
                'reply.putInt("terminationSelfPid", Process.myPid())', 'reply.putBoolean("quiescentBeforeDeath", true)',
                'if (die && delivered)', 'Process.killProcess(Process.myPid())'), "Exact authenticated owned service/self-PID death required")
    cleanup = test.split('fun cleanup(primary: Throwable?)', 1)[1].split('private inner class PendingNativeOpen', 1)[0]
    require(contains(cleanup, 'first.addSuppressed(failure)', 'attempt { pendingOpen?.close() }', 'attempt { source?.close()',
            'attempt { closeCaller() }', 'attempt { root?.releaseBookmark(context) }', 'attempt { ui?.close() }',
            'originalAccessibilityFlags, instrumentation.uiAutomation.serviceInfo.flags', 'request("revoke", session)',
            'persistedUriPermissions.any { it.uri == tree }', 'openDeviceDescriptorsFor(it)',
            'request("stop", session).getBundle("provider")', 'request("stop", session).getBundle("backend")',
            'provider).dieAndObserveBinderDeath(session)', 'control).dieAndObserveBinderDeath(session)',
            'attempt { provider?.close() }', 'attempt { control?.close() }', 'if (primary == null) cleanup?.let { throw it }'),
            "Independent unconditional native/source/grant/UI/process/thread cleanup must retain primary/suppressed errors")
    code = "\n".join(texts[JAVA + name + ".java"] for name in JAVA_NAMES) + "\n" + test + caller + endpoint
    require(not any(token in code for token in ('grantUriPermission(', 'Runtime.getRuntime', 'ProcessBuilder(', 'getByName(',
            'HttpURLConnection', 'new URL(', 'FLAG_LOCAL_ONLY', 'new File(', 'readBytes()', 'deleteRecursively()',
            'resetCounters', 'clearJournal', 'System.out.', 'System.err.', 'android.util.Log')),
            "Manual grants/DNS/host shell/body-file fallback/local-only/global cleanup/counter reset/raw console are forbidden")


def validate_source_receipt(receipt: dict) -> None:
    require(isinstance(receipt, dict) and set(receipt) == {"source_policy_verified", "source_inputs", "source_inputs_sha256",
            "native_or_compile_success_inferred", "scope"} and receipt.get("source_policy_verified") is True and
            receipt.get("native_or_compile_success_inferred") is False and receipt.get("scope") == "controlled-loopback-source-only",
            "Explicit NEW source-only remote witness required")
    inputs = receipt.get("source_inputs")
    require(isinstance(inputs, dict) and tuple(sorted(inputs)) == SOURCE_FILES and
            all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in inputs.values()) and
            receipt.get("source_inputs_sha256") == lt.input_digest(inputs), "Exact finite held remote source map required")


def source_contract(root: Path) -> dict:
    import android_io_remote_routing_source_projection as remote_routing
    remote_routing.validate_current_sources(root)
    texts, inputs = {}, {}
    for relative in SOURCE_FILES:
        path = lt.safe_path(root, relative)
        require(path.is_file() and 0 < path.stat().st_size <= 524288, "Bounded regular owned remote source required")
        payload = path.read_bytes(); inputs[relative] = hashlib.sha256(payload).hexdigest(); texts[relative] = payload.decode("utf-8")
    normalize_reporter_manifest(texts[REPORTER_MANIFEST].encode("utf-8"))
    for relative, digest in REUSED_PINS.items():
        require(inputs[relative] == digest, "Accepted endpoint/UI/descriptor/system-caller source must remain byte-identical")
    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode("utf-8"), compiled=False)
    validate_sources(texts)
    build = texts[FIXTURE + "/build.gradle.kts"]
    require(contains(build, 'applicationId = "' + PACKAGE + '"', 'namespace = "' + PACKAGE + '"',
            'compileSdk = libs.versions.android.compileSdk.get().toInt()', 'minSdk = libs.versions.android.minSdk.get().toInt()',
            'targetSdk = libs.versions.android.compileSdk.get().toInt()', 'JavaVersion.VERSION_17') and
            'dependencies {' not in build and 'from(files("../../../gradle/libs.versions.toml"))' in texts[FIXTURE + "/settings.gradle.kts"] and
            contains(texts["gradle/libs.versions.toml"], 'android-minSdk = "23"', 'android-compileSdk = "37"'),
            "Exact catalog/JDK17 SDK-only helper required, no extra library/dependency/version fallback")
    require(all(lt.sha256(lt.safe_path(root, relative)) == digest for relative, digest in inputs.items()),
            "Remote source changed during readback")
    receipt = {"source_policy_verified": True, "source_inputs": inputs, "source_inputs_sha256": lt.input_digest(inputs),
               "native_or_compile_success_inferred": False, "scope": "controlled-loopback-source-only"}
    validate_source_receipt(receipt); return receipt


def validate_prepared_receipt(receipt: dict, expected_source: dict | None = None) -> None:
    require(isinstance(receipt, dict) and receipt.get("package") == PACKAGE and receipt.get("source_fixture") == FIXTURE and
            receipt.get("prepare_status") == "passed" and type(receipt.get("verification_api_level")) is int and
            receipt["verification_api_level"] == 35 and
            receipt.get("recipient_installed") is True and receipt.get("manual_URI_grant") is False and
            receipt.get("automatic_runtime_permission_grant") is False and receipt.get("native_or_consumer_success_inferred") is False,
            "Only exact installed API35 source-helper preparation, never native/consumer acceptance")
    digest, installed, policy = receipt.get("source_apk_sha256"), receipt.get("installed_readback"), receipt.get("apk_policy")
    require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) and isinstance(installed, dict) and
            installed.get("apk_sha256") == digest and installed.get("exact_one_APK_path_observed") is True and
            isinstance(policy, dict) and all(policy.get(key) is True for key in ("compiled_manifest_inspected",
                "content_requires_android_grant", "signature_control_only", "INTERNET_only", "no_helper_grant_activity")) and
            policy.get("native_or_consumer_success_inferred") is False, "Actual source APK/manifest/installed byte identity required")
    require(isinstance(policy.get("certificate_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", policy["certificate_sha256"]) and
            policy["certificate_sha256"] == policy.get("private_key_certificate_sha256") and policy.get("apk_signer_revision") == SIGNER_REVISION and
            type(policy.get("signature_verification_min_sdk_version")) is type(policy.get("signature_verification_max_sdk_version")) is int and
            policy["signature_verification_min_sdk_version"] == policy["signature_verification_max_sdk_version"] == 35,
            "Exact actual private-key signer and explicit API35-only APK signature witness required")
    validate_source_receipt(receipt.get("source_contract"))
    require(expected_source is None or receipt["source_contract"] == expected_source, "Remote helper and reporter held source witnesses disagree")


class OwnedRemoteIoDocuments(OwnedIoDocuments):
    """Own NEW helper before prepare; lead's controller must always call close even on partial failure."""
    PACKAGE, FIXTURE, OUTPUT = PACKAGE, FIXTURE, "io-remote-documents"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.receipt.update(native_or_consumer_success_inferred=False,
            scope="Controlled real loopback TCP DocumentsProvider in one separate helper UID/two native processes only. Not commercial cloud/Downloads/provider restart/Maven consumer/physical/minimum/API-ABI/security/release certification.")

    def inspect_apk(self, apk: Path) -> dict:
        analyzer, signer = self.inspectors()
        inspected = self.host([str(analyzer), "manifest", "print", str(apk)])
        require(inspected.returncode == 0 and not inspected.stderr.strip(), "Actual compiled remote helper manifest unavailable")
        policy = validate_manifest(inspected.stdout, compiled=True)
        certificate = signer_certificate(self.host([str(signer), "verify", "--verbose", "--print-certs",
            "--min-sdk-version", "35", "--max-sdk-version", "35", str(apk)]))
        key = Path(self.environment["ANDROID_USER_HOME"]) / "debug.keystore"
        checked = lt.safe_path(self.root, key.relative_to(self.root).as_posix()); before = checked.stat()
        require(checked.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 65536, "Exact private controller debug key required")
        exported = self.host(["keytool", "-exportcert", "-keystore", str(checked), "-alias", "androiddebugkey", "-storepass", "android"])
        require(exported.returncode == 0 and not exported.stderr.strip() and 0 < len(exported.stdout) <= 16384,
                "Actual private debug-key public certificate unavailable")
        after = checked.stat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        require(tuple(getattr(before, field) for field in fields) == tuple(getattr(after, field) for field in fields),
                "Exact private key changed during certificate readback")
        expected = hashlib.sha256(exported.stdout).hexdigest()
        require(certificate == expected, "Remote helper signer disagrees with exact owned private key")
        return policy | {"certificate_sha256": certificate, "private_key_certificate_sha256": expected,
            "apk_signer_revision": SIGNER_REVISION, "signature_verification_min_sdk_version": 35,
            "signature_verification_max_sdk_version": 35, "raw_manifest_certificate_key_or_paths_uploaded": False}

    def prepare(self) -> dict:
        self.receipt["prepare_status"] = "running"
        try:
            self.receipt["source_contract"] = source_contract(self.root)
            self.inspectors() # Fixed official inspector/signer refusal before any helper/reporter compilation.
            require(self.readback() is None, "Prior/foreign remote helper exists; never replace it")
            command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain",
                "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", "-p", self.FIXTURE, "assembleDebug"]
            execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
            self.receipt.update(assembly_command=command, assembly=execution)
            require(execution["exit_code"] == 0 and not execution.get("stop_reason"), "Remote helper assembly failed")
            apk = metadata_apk(self.root, fixture=self.FIXTURE, package=self.PACKAGE); self.digest = lt.sha256(apk)
            self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size)
            self.receipt["apk_policy"] = self.inspect_apk(apk) # Real compiled manifest/private-key identity BEFORE installation/reporter.
            require(lt.sha256(apk) == self.digest and source_contract(self.root) == self.receipt["source_contract"],
                    "Remote source/APK changed during preparation")
            self.install_attempted = True
            installed = self.control("install", "-t", str(apk), timeout=120) # No manual grants, -g, -r or replacement.
            actual = self.readback() # Reconcile even uncertain/failed install before identity-only always cleanup.
            match = actual is not None and actual["apk_sha256"] == self.digest
            self.receipt.update(install_exit_code=installed.returncode, installed_readback=actual, recipient_installed=match,
                automatic_runtime_permission_grant=False, native_signature_UID_and_URI_reads_still_required=True)
            require(installed.returncode == 0 and b"Success" in installed.stdout.splitlines() and match,
                    "Owned remote installation/actual readback failed; no blind retry")
            require(source_contract(self.root) == self.receipt["source_contract"], "Remote source changed after install")
            self.receipt["prepare_status"] = "passed"; validate_prepared_receipt(self.receipt)
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as failure:
            self.receipt.update(prepare_status="failed", prepare_error=type(failure).__name__); raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)
