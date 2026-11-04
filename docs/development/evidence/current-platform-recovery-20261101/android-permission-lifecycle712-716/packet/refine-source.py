from pathlib import Path
R=Path('/root/nativecmpkit-worktrees/android-permission-lifecycle')
def edit(rel,old,new):
 p=R/rel;s=p.read_text();assert s.count(old)==1,(rel,s.count(old),old[:60]);p.write_text(s.replace(old,new))
C='scripts/ci/android_permission_lifecycle_contract.py'
edit(C,'import hashlib\n','import hashlib\nimport json\n')
edit(C,'SOURCE_FILES = tuple(sorted((\n','''SOURCE_FILES = tuple(sorted((
    ".github/workflows/gradle.yml",
    *("scripts/ci/" + name + ".py" for name in ("library_tests", "android_device_tests", "workflow_matrix",
        "android_storage_probe", "android_permission_lifecycle", "android_permission_lifecycle_contract",
        "android_share_recipient", "android_geo_probe", "android_io_documents", "android_permission_demo")),
''')
edit(C,'("AndroidPermissionRequestPlan", "MutablePermissionState.android", "MutableMultiplePermissionsState.android", "PermissionsUtil.android")),','''("AndroidPermissionRegistry", "AndroidPermissionRequestPlan", "MutablePermissionState.android", "MutableMultiplePermissionsState.android", "PermissionsUtil.android")),
    *(MODULE + "/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/" + name + ".kt" for name in
      ("PermissionState", "MultiplePermissionsState", "PermissionDetails", "PermissionRequestGate",
       "MutablePermissionState", "MutableMultiplePermissionsState")),''')
edit(C,'def test_filter(focus: str) -> str:\n','''def validate_request(api_level: int, modules: tuple[str, ...], focus: str) -> None:
    require(type(api_level) is int and api_level == API and type(modules) is tuple and modules == (MODULE,) and
            isinstance(focus, str) and focus in FOCUSES, "Exact integer API35/one permission core/finite focus required")


def validate_metadata(payload: bytes) -> str:
    """One inert metadata record for this NEW package; never expands the old whitelist."""
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Bounded actual APK metadata required")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate actual metadata identity")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("Nonfinite APK metadata")
    data = json.loads(payload, object_pairs_hook=unique, parse_constant=nonfinite)
    require(isinstance(data, dict) and isinstance(data.get("artifactType"), dict) and
            data["artifactType"].get("type") == "APK" and data.get("applicationId") == PACKAGE and
            data.get("variantName") == "debug", "Exact own debug APK metadata required")
    rows = data.get("elements")
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "Exactly one APK metadata element required")
    row = rows[0]
    name = row.get("outputFile")
    require(row.get("type") == "SINGLE" and row.get("filters") == [] and isinstance(name, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]+\\.apk", name) and ".." not in name, "Unsplit own APK basename required")
    return name


def validate_reporter_source(payload: bytes) -> None:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536 and
            b"<!DOCTYPE" not in payload and b"<!ENTITY" not in payload, "Bounded entity-free reporter source required")
    root = ET.fromstring(payload)
    names = [node.get(ANDROID + "name") for node in root.findall("uses-permission")]
    controls = {PERMISSION, "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO",
                "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe.CONTROL_STORAGE"}
    require(root.tag == "manifest" and root.get(ANDROID + "sharedUserId") is None and
            root.get(ANDROID + "sharedUserMaxSdkVersion") is None and len(names) == len(set(names)) and set(names) == controls and
            all(set(n.attrib) == {ANDROID + "name"} and not list(n) for n in root.findall("uses-permission")) and
            not root.findall("uses-permission-sdk-23"), "Reporter cannot acquire runtime or arbitrary signature permissions")
    queries = root.findall("queries")
    require(len(queries) == 1, "One reporter visibility declaration required")
    packages = [node.get(ANDROID + "name") for node in queries[0].findall("package")]
    require(len(packages) == len(set(packages)) and {PACKAGE, "com.android.settings"} <= set(packages),
            "Actual helper and Settings visibility required")


def test_filter(focus: str) -> str:
''')
edit(C,'require(focus in FOCUSES, "Unknown or unfocused permission lifecycle request")','require(isinstance(focus, str) and focus in FOCUSES, "Unknown or unfocused permission lifecycle request")')
edit(C,'(before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==\n                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),','(before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode, before.st_nlink) ==\n                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode, after.st_nlink),')
edit(C,'    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)\n','''    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)
    validate_reporter_source(texts[MODULE + "/src/androidDeviceTest/AndroidManifest.xml"].encode())
    expected_fixture_sources = {FIXTURE + "/src/main/AndroidManifest.xml",
        APPLICATION_KOTLIN + "PermissionLifecycleActivity.kt", APPLICATION_KOTLIN + "PermissionLifecycleService.kt"}
    actual_fixture_sources = set()
    for path in (root / FIXTURE / "src").rglob("*"):
        require(not path.is_symlink(), "No linked source fixture inventory")
        if path.is_file():
            actual_fixture_sources.add(path.relative_to(root).as_posix())
        require(len(actual_fixture_sources) <= len(expected_fixture_sources), "Unexpected source fixture input")
    require(actual_fixture_sources == expected_fixture_sources, "Exact three helper source inputs required")
''')
edit(C,'def validate_prepared_receipt(receipt: dict, expected_source: dict, api_level: int = API) -> None:\n','def validate_prepared_receipt(receipt: dict, expected_source: dict, api_level: int = API, *, focus: str) -> None:\n')
edit(C,'    validate_source_receipt(expected_source)\n    require(type(api_level) is int and api_level == API and isinstance(receipt, dict) and\n','    validate_source_receipt(expected_source)\n    validate_request(api_level, (MODULE,), focus)\n    require(isinstance(receipt, dict) and receipt.get("focus") == focus and\n')
edit(C,'receipt.get("automatic_runtime_permission_grant") is False and receipt.get("source_contract") == expected_source,','receipt.get("automatic_runtime_permission_grant") is False and receipt.get("source_contract") == expected_source and\n            type(receipt.get("source_apk_bytes")) is int and 0 < receipt["source_apk_bytes"] < 256 * 1024**2,')
P='scripts/ci/android_permission_lifecycle.py'
edit(P,'import os\n','import os\nimport stat\n')
edit(P,'from android_geo_probe import metadata_apk\n','')
edit(P,'API, PACKAGE, FIXTURE, source_contract, validate_manifest, validate_prepared_receipt, require,','API, MODULE, PACKAGE, FIXTURE, source_contract, validate_manifest, validate_metadata, validate_request, validate_prepared_receipt, require,')
edit(P,'    def __init__(self, *args, api_level: int, **kwargs):\n        require(type(api_level) is int and api_level == API, "Only exact integer API35 is admitted")\n','    def __init__(self, *args, api_level: int, focus: str, **kwargs):\n        validate_request(api_level, (MODULE,), focus)\n')
edit(P,'self.receipt.update(verification_api_level=API, prepare_status=', 'self.receipt.update(verification_api_level=API, focus=focus, prepare_status=')
edit(P,'    def inspect_apk(self, apk: Path) -> dict:\n','''    def metadata_apk(self) -> Path:
        # Do not expand android_geo_probe's accepted historical fixture whitelist.
        base = lt.safe_path(self.root, FIXTURE + "/build/outputs/apk/debug")
        metadata = lt.safe_path(self.root, (base / "output-metadata.json").relative_to(self.root).as_posix())
        before = metadata.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 65536,
                "Exact bounded regular metadata required")
        payload = metadata.read_bytes()
        after = metadata.lstat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Metadata changed during readback")
        name = validate_metadata(payload)
        apk = lt.safe_path(self.root, (base / name).relative_to(self.root).as_posix())
        identity = apk.lstat()
        require(stat.S_ISREG(identity.st_mode) and identity.st_nlink == 1 and 0 < identity.st_size < 256 * 1024**2,
                "Actual bounded regular unsplit APK required")
        return apk

    def inspect_apk(self, apk: Path) -> dict:
''')
edit(P,'        before = key.stat()\n        require(key.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 65536,','        before = key.lstat()\n        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 65536 and\n                key.parent.is_dir() and key.parent.stat().st_mode & 0o077 == 0,')
edit(P,'        after = key.stat()\n','        after = key.lstat()\n')
edit(P,'            apk = metadata_apk(self.root, fixture=FIXTURE, package=PACKAGE)\n','            apk = self.metadata_apk()\n')
edit(P,'            validate_prepared_receipt(self.receipt, contract, API)\n','            validate_prepared_receipt(self.receipt, contract, API, focus=self.receipt["focus"])\n')
edit(P,'        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as failure:\n','        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as failure:\n')
L='scripts/ci/library_tests.py'
edit(L,'                test_plan["android_permission_lifecycle"]["source_contract"])\n','                test_plan["android_permission_lifecycle"]["source_contract"], focus=test_plan["explicit_test_focus"])\n')
edit(L,'                test_plan["android_permission_lifecycle"]["source_contract"], int(actual_api))\n','                test_plan["android_permission_lifecycle"]["source_contract"], int(actual_api), focus=focus)\n')
D='scripts/ci/android_device_tests.py'
edit(D,'lambda: process.poll() is None and avd_name(home) == name, environment=env, api_level=api_level)\n            result["permission_lifecycle"]','lambda: process.poll() is None and avd_name(home) == name, environment=env, api_level=api_level, focus=focus)\n            result["permission_lifecycle"]')
edit(D,'                plan["android_permission_lifecycle"]["source_contract"], api_level)\n','                plan["android_permission_lifecycle"]["source_contract"], api_level, focus=focus)\n')
edit(D,'        if type(api_level) is not int or api_level != 35 or modules != (permission_lifecycle_contract.MODULE,):\n            raise ValueError("Permission lifecycle requires exact integer API35, one finite focus and permission core only")\n','        permission_lifecycle_contract.validate_request(api_level, modules, focus)\n')
U='calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/PermissionLifecycleSystemUi.kt'
edit(U,'                    assertTrue(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK))\n','''                    assertTrue(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK))
                    val remaining = deadline - SystemClock.elapsedRealtime()
                    check(remaining > 0) { "Native Back exceeded its original deadline" }
                    // Observe actual OS idleness before another fresh root/Back. Never spam
                    // Back against a stale in-flight Settings transition and close the host.
                    automation.waitForIdle(250, minOf(4000L, remaining))
''')
edit(U,'            sleepBefore(deadline, 200)\n','            sleepBefore(deadline, 40)\n')
B='calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/OwnedPermissionLifecycle.kt'
edit(B,'    private var nativePid: Int? = null\n','    private var nativePid: Int? = null\n    private var activityGeneration: String? = null\n')
edit(B,'                service.linkToDeath(death, 0)\n','                assertNull(binder, "A replacement lifecycle Binder cannot be admitted")\n                service.linkToDeath(death, 0)\n')
edit(B,'            } catch (failure: Exception) { protocolError = "Invalid lifecycle service admission" }','            } catch (failure: Throwable) { protocolError = "Invalid lifecycle service admission" }')
edit(B,'            protocolError = "Owned lifecycle service disconnected"\n','            protocolError = "Owned lifecycle service disconnected"\n            admission.countDown()\n')
edit(B,'                    assertNotNull(it.getString("activityGeneration"))\n','''                    val activeGeneration = assertNotNull(it.getString("activityGeneration"))
                    assertTrue(activeGeneration.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))
                    if (activityGeneration == null) activityGeneration = activeGeneration else assertEquals(activityGeneration, activeGeneration)
''')
edit(B,'        try {\n            if (bound && endpoint != null && protocolError == null) {\n','        try {\n            assertNull(protocolError, "A lifecycle protocol/death failure cannot pass as clean native disposal")\n            if (bound && endpoint != null) {\n')
T='calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionLifecycleDeviceTest.kt'
edit(T,'    @After fun tearDown() {\n        try { if (::consumer.isInitialized) consumer.close() }\n        finally { if (::ui.isInitialized) ui.close() }\n    }','''    @After fun tearDown() {
        var failure: Throwable? = null
        try { if (::consumer.isInitialized) consumer.close() }
        catch (error: Throwable) { failure = error }
        finally {
            try { if (::ui.isInitialized) ui.close() }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
        }
        failure?.let { throw it }
    }''')
edit(T,'        val granted = consumer.await { it.getBundle("Notification")?.getInt("callbacks") == 1 }\n','''        val granted = consumer.await { it.getBundle("Notification")?.getInt("callbacks") == 1 &&
            it.getBoolean(Manifest.permission.POST_NOTIFICATIONS) && it.getBundle("Notification")?.getBoolean("granted") == true &&
            it.getBundle("batch.Notification")?.getBoolean("granted") == true && it.getBoolean("resumed") && it.getBoolean("focused") }
''')
print('Source refinement applied; no compiler/native/planner/controller/Git execution.')
