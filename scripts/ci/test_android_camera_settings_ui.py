"""Important supported-Settings source/models only; not Android/UI/native outcomes."""
from pathlib import Path
import os
import re
import subprocess
from copy import deepcopy
import unittest

ROOT = Path(os.environ.get("NATIVECMPKIT_CAMERA_UI_ROOT", Path(__file__).resolve().parents[2]))
PACKAGE = "com.android.settings"
COMPONENT = PACKAGE + "/.Settings$DevelopmentSettingsActivity"
ACTION = "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
HELPER = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt"
UI = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt"
NONCE = "a" * 32
MARKER = "nativecmpkit-settings-" + NONCE
HEADER = "ACTIVITY MANAGER RECENT TASKS (dumpsys activity recents)"


def source(path=UI):
    return (ROOT / path).read_text(encoding="utf-8")


def modeled_complete(text, marker=MARKER):
    if len(text.encode()) > 65536 or any(c in text for c in "\r\0\x1b"):
        raise ValueError("Malformed bounded reply")
    lines = text.splitlines()
    if not lines or lines[-1] != marker + "-0" or sum(marker in x for x in lines) != 1:
        raise ValueError("Missing exact successful completion")
    return lines[:-1]


def modeled_recents(text, nonce=NONCE):
    lines = modeled_complete(text)
    if (len(lines) < 5 or lines[0] != HEADER or lines.count(HEADER) != 1 or
        not re.fullmatch(r"mRecentsUid=[0-9]+", lines[1]) or
        not re.fullmatch(r"mRecentsComponent=ComponentInfo\{[^\r\n{}]+\}", lines[2]) or
        not re.fullmatch(r"mFreezeTaskListReordering=(true|false)", lines[3]) or
        not re.fullmatch(r"mFreezeTaskListReorderingPendingTimeout=(true|false)", lines[4])):
        raise ValueError("Incomplete source-backed recents query")
    rest = lines[5:]
    if not rest or rest == ["  (nothing)"]:
        return []
    if rest[0] != "  Recent tasks:":
        raise ValueError("Visible-only/unknown/hidden tasks")
    if rest.count("  Recent tasks:") != 1 or rest.count("  Visible recent tasks (most recent first):") > 1:
        raise ValueError("Duplicate source boundary")
    raw = rest[1:]
    if "  Visible recent tasks (most recent first):" in raw:
        raw = raw[:raw.index("  Visible recent tasks (most recent first):")]
        while raw and not raw[-1]: raw.pop()
    starts = [i for i, row in enumerate(raw) if row.startswith("  * Recent #")]
    if not starts or starts[0] != 0:
        raise ValueError("Missing raw task")
    result = []
    for start, end in zip(starts, starts[1:] + [len(raw)]):
        block = raw[start:end]
        match = re.fullmatch(r"  \* Recent #([0-9]+): Task\{[a-f0-9]+ #([1-9][0-9]*) type=standard[^{}]*\}", block[0])
        if not match or not re.fullmatch(r"    lastActiveTime=[0-9]+ \(inactive for [0-9]+s\)", block[-1]):
            raise ValueError("Incomplete exact raw task")
        required = [r"    userId=([0-9]+) effectiveUid=(\S+) mCallingUid=(\S+) mUserSetupComplete=(true|false) mCallingPackage=(\S+) mCallingFeatureId=(\S+)",
                    r"    taskId=([1-9][0-9]*) rootTaskId=([1-9][0-9]*)"]
        values = []
        for pattern in required:
            rows = [re.fullmatch(pattern, x) for x in block[1:] if re.fullmatch(pattern, x)]
            if len(rows) != 1: raise ValueError("Unknown/duplicate identity")
            values.append(rows[0].groups())
        user, uid, calling, setup, package, feature = values[0]
        task, _ = values[1]
        intents = [x for x in block if x.startswith("    intent=")]
        components = [x for x in block if x.startswith("    mActivityComponent=")]
        if len(intents) != 1 or len(components) != 1 or task != match.group(2):
            raise ValueError("Missing/duplicate exact task identity")
        expected = f"    intent={{act={ACTION} id={nonce} flg=0x18000000 cmp={COMPONENT}}}"
        if intents[0] != expected or components[0] != "    mActivityComponent=" + COMPONENT:
            raise ValueError("Not this nonce-bound settings lease")
        if (user, uid, calling, setup, package, feature) != ("0", "1000", "2000", "true", "com.android.shell", "null"):
            raise ValueError("Foreign task/UID/user/caller")
        result.append(int(task))
    if len(result) != len(set(result)) or len(result) != 1:
        raise ValueError("Competing/duplicate settings tasks")
    return result


def fixture(*, present=True, visible=False):
    rows = [HEADER, "mRecentsUid=10123", "mRecentsComponent=ComponentInfo{com.android.launcher3/.QuickstepLauncher}",
            "mFreezeTaskListReordering=false", "mFreezeTaskListReorderingPendingTimeout=false"]
    if present:
        rows += ["  Recent tasks:", "  * Recent #0: Task{abcd #42 type=standard A=1000:com.android.settings}",
                 "    userId=0 effectiveUid=1000 mCallingUid=2000 mUserSetupComplete=true mCallingPackage=com.android.shell mCallingFeatureId=null",
                 "    affinity=1000:com.android.settings",
                 f"    intent={{act={ACTION} id={NONCE} flg=0x18000000 cmp={COMPONENT}}}",
                 "    mActivityComponent=" + COMPONENT, "    Activities=[]", "    taskId=42 rootTaskId=1",
                 "    hasChildPipActivity=false", "    mHasBeenVisible=true", "    mResizeMode=RESIZE_MODE_RESIZEABLE mSupportsPictureInPicture=false isResizeable=true",
                 "    lastActiveTime=123 (inactive for 0s)"]
    if visible:
        rows += ["", "  Visible recent tasks (most recent first):", "  * RecentTaskInfo #0: modeled unrelated visibility fields"]
    return "\n".join(rows + [MARKER + "-0"])


def modeled_live_tasks(text):
    lines = [x for x in modeled_complete(text) if x]
    if not lines: raise ValueError("No complete live-root snapshot")
    roots = [i for i, x in enumerate(lines) if x.startswith("RootTask id=")]
    if not roots or roots[0] != 0: raise ValueError("Missing native roots")
    ids, settings, children = set(), set(), set()
    bounds = r"\[-?[0-9]+,-?[0-9]+]\[-?[0-9]+,-?[0-9]+]"
    for start, end in zip(roots, roots[1:] + [len(lines)]):
        block = lines[start:end]
        root = re.fullmatch(r"RootTask id=([0-9]+) bounds=" + bounds + r" displayId=[0-9]+ userId=[0-9]+", block[0])
        if len(block) < 2 or not root or not block[1].startswith(" configuration={") or not block[1].endswith("}"):
            raise ValueError("Incomplete root/configuration")
        ids.add(int(root.group(1)))
        for row in block[2:]:
            child = re.fullmatch(r"  taskId=([0-9]+): ([^\s]+)(?: bounds=" + bounds + r")? userId=[0-9]+ visible=(true|false)(?: topActivity=ComponentInfo\{([^{}]+)})?", row)
            if not child: raise ValueError("Unknown live task row")
            task = int(child.group(1)); name = child.group(2); top = child.group(4) or ""
            if task in children or name == "unknown": raise ValueError("Unknown/duplicate task ownership")
            ids.add(task); children.add(task)
            if name == PACKAGE or name.startswith(PACKAGE + "/") or top.startswith(PACKAGE + "/"): settings.add(task)
    return ids, settings


def live_fixture(*, settings=False):
    name = PACKAGE + "/com.android.settings.Settings$DevelopmentSettingsActivity" if settings else "com.android.launcher3/com.android.launcher3.uioverrides.QuickstepLauncher"
    rows = ["RootTask id=1 bounds=[0,0][1080,1920] displayId=0 userId=0", " configuration={modeled native configuration}",
            "  taskId=42: " + name + " bounds=[0,0][1080,1920] userId=0 visible=true topActivity=ComponentInfo{" + name + "}", ""]
    return "\n".join(rows + [MARKER + "-0"])


def modeled_restore(original, current, *, armed, clicked, ui, master="1"):
    if master != "1" or original[0] != (original[1] == "1"):
        raise ValueError("Master/native baseline unknown")
    permitted = {(True, "1")} if armed else {original, (original[0], "1"), (True, "1")}
    if current not in permitted or ui != (current[1] == "1"):
        raise ValueError("Foreign/unverified current state")
    desired = original[0]
    if clicked != (ui != desired):
        raise ValueError("No double/fabricated toggle")
    after = (desired, "1" if desired else "0") if clicked else current
    if after[0] != desired:
        raise ValueError("UI-only native acceptance forbidden")
    deleted = original[1] == "null" and clicked
    if deleted:
        if after != (False, "0"): raise ValueError("No owned zero")
        after = (False, "null")
    if after != original: raise ValueError("Not exactly restored")
    return after, deleted


def modeled_selection(nodes):
    titles = [i for i, n in enumerate(nodes) if n.get("text") == "installed title"]
    summaries = [i for i, n in enumerate(nodes) if n.get("text") == "installed summary"]
    if len(titles) != 1 or len(summaries) != 1:
        raise ValueError("Missing/duplicate installed preference text")
    if nodes[titles[0]].get("id") != "android:id/title" or nodes[summaries[0]].get("id") != "android:id/summary":
        raise ValueError("Wrong native resource identity")
    def below(child, parent):
        seen = set()
        while child >= 0:
            if child in seen: raise ValueError("Cyclic/unknown tree")
            seen.add(child)
            if child == parent: return True
            child = nodes[child]["parent"]
        return False
    parent = nodes[titles[0]]["parent"]
    while parent >= 0:
        row = nodes[parent]
        if row.get("clickable") and below(summaries[0], parent):
            children = [n for i, n in enumerate(nodes) if below(i, parent)]
            if sum(n.get("id") == "android:id/title" for n in children) != 1:
                raise ValueError("Broad/cross-row click")
            switches = [n for n in children if n.get("id") == "com.android.settings:id/switchWidget"]
            if len(switches) != 1: raise ValueError("Missing/duplicate installed switch")
            switch = switches[0]
            if switch.get("class") not in ("android.widget.Switch", "androidx.appcompat.widget.SwitchCompat"):
                raise ValueError("Wrong native switch")
            if not switch.get("checkable") or not all(n.get("enabled") and n.get("visible") and n.get("package") == PACKAGE for n in (row, switch)):
                raise ValueError("Foreign/disabled/invisible node")
            if not row.get("click_action"): raise ValueError("Not actionable")
            return parent
        parent = row["parent"]
    raise ValueError("No exact actionable row")


def ui_fixture():
    shared = dict(package=PACKAGE, enabled=True, visible=True)
    return [dict(shared, parent=-1, id="root", clickable=False),
            dict(shared, parent=0, id="row", clickable=True, click_action=True),
            dict(shared, parent=1, id="android:id/title", text="installed title"),
            dict(shared, parent=1, id="android:id/summary", text="installed summary"),
            dict(shared, parent=1, id="com.android.settings:id/switchWidget", checkable=True, **{"class":"android.widget.Switch"})]


def modeled_flags(original, current, *, configured=True, restoration_attempted=False, actual=None):
    requested = original | 2 | 16 | 64  # Modeled flag bits, not Android constants/permission adoption.
    if restoration_attempted or (current != requested if configured else current not in (original, requested)):
        raise ValueError("Foreign flags or uncertain restoration cannot be retried")
    if actual != original: raise ValueError("Restoration not natively read back")
    return actual


class CameraSettingsUiSourceTests(unittest.TestCase):
    def test_new_ui_helper_is_an_explicit_required_confined_finite_input(self):
        text = source("scripts/ci/library_tests.py")
        self.assertIn('ANDROID_CAMERA_SETTINGS_UI_SOURCE = "' + UI + '"', text)
        self.assertEqual(2, text.count("ANDROID_CAMERA_ALWAYS_FINISH_SOURCE, ANDROID_CAMERA_SETTINGS_UI_SOURCE)"))
        self.assertIn("def validate_test_focus(", text)
        self.assertIn("ANDROID_CAMERA_DONT_KEEP_FOCUS", text)

    def test_hidden_transaction_guessing_and_scalar_write_are_removed_not_bypassed(self):
        combined = source(HELPER) + source()
        for token in ("Class.forName", "TRANSACTION_setAlwaysFinish", "getDeclaredField", "service call activity", "adoptShellPermissionIdentity", "hidden_api_policy", "setHiddenApiExemptions", "settings put global always_finish_activities"):
            self.assertNotIn(token, combined)
        self.assertIn("OwnedDeveloperSettingsUi(pm, ui, shell)", source(HELPER))

    def test_exact_platform_settings_component_export_uid_and_fragment_are_required(self):
        text = source()
        for token in ('"com.android.settings.Settings\\$DevelopmentSettingsActivity"', '"com.android.settings.development.DevelopmentSettingsDashboardFragment"', "applicationInfo.uid == 1000", "ApplicationInfo.FLAG_SYSTEM", 'checkSignatures("android", SETTINGS_PACKAGE)', "ActivityInfo.LAUNCH_MULTIPLE", "info.enabled", "info.exported", "info.permission == null", "getComponentEnabledSetting(component)", "getApplicationEnabledSetting(SETTINGS_PACKAGE)"):
            self.assertIn(token, text)
        manifest = (ROOT / "calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml").read_text()
        self.assertEqual(1, manifest.count('<package android:name="com.android.settings" />'))

    def test_native_shell_task_permissions_are_observed_not_adopted_or_granted(self):
        text = source()
        for permission in ("DUMP", "MANAGE_ACTIVITY_TASKS", "REMOVE_TASKS"):
            self.assertIn('checkPermission("android.permission.' + permission + '", "com.android.shell") == PackageManager.PERMISSION_GRANTED', text)
        for forbidden in ("adoptShellPermissionIdentity", "pm grant", "grantRuntimePermission", "su "):
            self.assertNotIn(forbidden, text)

    def test_developer_master_is_exact_original_one_and_never_toggled(self):
        text = source()
        self.assertIn('shell("settings get global development_settings_enabled", CONTROL_BYTES) == "1"', text)
        self.assertGreaterEqual(text.count("requireMaster()"), 5)
        self.assertNotIn("settings put", text)
        self.assertNotIn("settings delete", text)
        self.assertNotIn("developer_settings_enabled", text)
        self.assertIn("settingsUi.requireMaster()", source(HELPER))

    def test_launch_is_fresh_nonce_bound_public_intent_with_source_backed_completion(self):
        text = source()
        for token in ("Intent(SETTINGS_ACTION)", ".setIdentifier(nonce)", "Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_MULTIPLE_TASK", "Intent.URI_INTENT_SCHEME", "check(readRecentTasks().isEmpty())", "activeLease = lease", "runComplete(\"am start -W --user 0 '$uri'\")", '"Starting: $intent"', '"Activity: ${component.flattenToShortString()}"', '"Status: ok"', '"Complete"'):
            self.assertIn(token, text)
        self.assertLess(text.index("activeLease = lease"), text.index('runComplete("am start'))
        self.assertIn('command.replace(" ", "\\${IFS}")', text)
        self.assertIn('"$marker-0"', text)
        self.assertIn('"sh -c $encoded;echo\\${IFS}$marker-\\$?"', text)

    def test_native_task_owner_and_top_resumed_are_exact_not_accessibility_only(self):
        text = source()
        for token in ('"dumpsys activity -p com.android.settings recents"', "RECENTS_HEADER", "RECENTS_VISIBLE", "lastActiveTime=", "effectiveUid=", "mCallingUid=", "mCallingPackage=", "mActivityComponent=", "taskId=", '"dumpsys activity top-resumed"', '"packageName=com.android.settings processName=com.android.settings"', '"launchedFromUid=2000 launchedFromPackage=com.android.shell launchedFromFeature=null userId=0"', '"state=RESUMED delayedResume=false finishing=false"', "lease.taskId", "check(rows.size == 1)"):
            self.assertIn(token, text)

    def test_installed_resource_title_summary_and_unique_checkable_row_precede_click(self):
        text = source()
        for token in ('getResourcesForApplication(SETTINGS_PACKAGE)', '"immediately_destroy_activities"', '"immediately_destroy_activities_summary"', '"android:id/title"', '"android:id/summary"', '"switchWidget"', "isCheckable", "isEnabled", "isVisibleToUser", "titles.size == 1", "summaries.size == 1", "switches.size == 1", "AccessibilityNodeInfo.ACTION_CLICK", "verifyNative(clicked)"):
            self.assertIn(token, text)
        self.assertLess(text.index("mutationAttempted = true"), text.index("performAction(AccessibilityNodeInfo.ACTION_CLICK)"))
        self.assertIn("check(switchChecked == expectedChecked)", text)
        self.assertIn("check(selected.widget.isChecked == enabled)", text)
        self.assertNotIn("tap ", text); self.assertNotIn("input ", text)

    def test_only_bound_owned_recycler_is_scrolled_no_fake_fragment_highlight(self):
        text = source()
        for token in ('"recycler_view"', '"androidx.recyclerview.widget.RecyclerView"', "scrolls++ < MAX_SCROLLS", "MAX_SCROLLS = 40", "MAX_NODES = 2048", "MAX_DEPTH = 32", "AccessibilityNodeInfo.ACTION_SCROLL_FORWARD", "assertTop(lease)", "nodes.forEach { it.recycle() }"):
            self.assertIn(token, text)
        self.assertNotIn(":settings:fragment_args_key", text)
        self.assertNotIn(":settings:show_fragment_args", text)

    def test_cleanup_proves_live_native_task_absence_not_only_recents_removal(self):
        text = source()
        for token in ('runComplete("am stack list")', "private fun readLiveTasks()", "live.settings.isEmpty()", "taskId !in live.ids", 'check(name != "unknown")', "check(lines.isNotEmpty())", "configuration={", "check(readLiveTasks().settings.isEmpty())"):
            self.assertIn(token, text)

    def test_only_exact_owned_task_removed_once_and_flags_restored_with_primary_errors(self):
        text = source()
        for token in ("lease.removalAttempted = true", 'runComplete("am stack remove $taskId")', "check(readRecentTasks().isEmpty())", "check(!lease.removalAttempted)", "flagsAttempted = true", "flagsRestorationAttempted = true", "originalFlags", "expectedFlags", "check(flags == expectedFlags)", "check(serviceFlags() == originalFlags)", "initial.addSuppressed(failure)", "finally", "cleanup { closeSettings() }", "cleanup { restoreFlags() }"):
            self.assertIn(token, text)
        self.assertLess(text.index("lease.removalAttempted = true"), text.index('runComplete("am stack remove'))
        self.assertLess(text.index("flagsAttempted = true"), text.index("ui.serviceInfo = requested"))
        self.assertNotIn("force-stop", text); self.assertNotIn("GLOBAL_ACTION_BACK", text)

    def test_ui_noop_restoration_preserves_original_absence_without_scalar_fallback(self):
        text = source(HELPER)
        for token in ("val clicked = setNative(original.native)", 'if (original.scalar == "null")', 'if (clicked)', "check(!original.native)", '"settings delete global always_finish_activities"', '== "Deleted 1 rows"', "check(readStableState() == original)", "settingsUi.setNative(enabled, before.scalar == \"1\")", "check(expected.native == enabled)", "if (clicked) State(enabled", "else before"):
            self.assertIn(token, text)
        self.assertNotIn("settings put", text)
        self.assertNotIn("recreate()", text)


class CameraSettingsUiBoundaryModelTests(unittest.TestCase):
    def test_completed_empty_and_owned_task_queries_are_distinguished(self):
        self.assertEqual([], modeled_recents(fixture(present=False)))
        self.assertEqual([42], modeled_recents(fixture()))
        self.assertEqual([42], modeled_recents(fixture(visible=True)))

    def test_missing_failed_duplicate_and_not_last_completion_are_refused(self):
        text = fixture()
        for bad in (text.rsplit("\n", 1)[0], text.replace(MARKER + "-0", MARKER + "-1"), text + "\n" + MARKER + "-0", text + "\ntrailing", text.replace(MARKER, MARKER + "foreign")):
            with self.subTest(kind=len(bad)), self.assertRaises(ValueError): modeled_recents(bad)

    def test_control_encoding_unbounded_and_foreign_headers_are_refused(self):
        for bad in (fixture() + "\0", fixture().replace("\n", "\r\n"), fixture() + "\x1b", fixture() + "x" * 65537, fixture().replace(HEADER, HEADER + " unknown")):
            with self.subTest(kind=len(bad)), self.assertRaises(ValueError): modeled_recents(bad)

    def test_missing_truncated_duplicate_and_reordered_raw_boundaries_are_refused(self):
        text = fixture()
        for bad in (text.replace("    lastActiveTime=123 (inactive for 0s)\n", ""), text.replace("mFreezeTaskListReordering=false\n", ""), text.replace("    taskId=42 rootTaskId=1", ""), text.replace("    taskId=42 rootTaskId=1", "    taskId=42 rootTaskId=1\n    taskId=42 rootTaskId=1"), text.replace("  Recent tasks:\n", ""), text.replace("  Recent tasks:\n", "  Recent tasks:\n  Recent tasks:\n")):
            with self.subTest(kind=len(bad)), self.assertRaises(ValueError): modeled_recents(bad)

    def test_native_uid_user_caller_component_nonce_and_flags_are_exact(self):
        text = fixture()
        for before, after in (("effectiveUid=1000", "effectiveUid=10123"), ("mCallingUid=2000", "mCallingUid=1000"), ("userId=0", "userId=10"), ("mCallingPackage=com.android.shell", "mCallingPackage=foreign"), ("mUserSetupComplete=true", "mUserSetupComplete=false"), (NONCE, "b" * 32), ("flg=0x18000000", "flg=0x10000000"), (".Settings$DevelopmentSettingsActivity", ".Settings$Foreign")):
            with self.subTest(before=before), self.assertRaises(ValueError): modeled_recents(text.replace(before, after))

    def test_task_id_mismatch_and_duplicate_owner_are_refused(self):
        text = fixture()
        with self.assertRaises(ValueError): modeled_recents(text.replace("taskId=42 rootTaskId=1", "taskId=43 rootTaskId=1"))
        lines = text.splitlines(); block = lines[6:-1]
        with self.assertRaises(ValueError): modeled_recents("\n".join(lines[:-1] + block + [lines[-1]]))

    def test_visible_only_foreign_nonce_does_not_create_raw_task_ownership(self):
        with self.assertRaises(ValueError): modeled_recents(fixture(present=False, visible=True))
        text = fixture(visible=True).replace("modeled unrelated visibility fields", "id=" + "b" * 32)
        self.assertEqual([42], modeled_recents(text))

    def test_live_task_id_and_settings_component_remain_observed_after_recents_removal(self):
        self.assertEqual(({1, 42}, {42}), modeled_live_tasks(live_fixture(settings=True)))
        self.assertEqual(({1, 42}, set()), modeled_live_tasks(live_fixture()))
        self.assertEqual([], modeled_recents(fixture(present=False)))
        self.assertIn(42, modeled_live_tasks(live_fixture(settings=True))[0])

    def test_empty_failed_truncated_unknown_and_duplicate_live_snapshots_are_refused(self):
        text = live_fixture()
        for bad in (MARKER + "-0", text.replace(" configuration={modeled native configuration}\n", ""), text.replace(MARKER + "-0", MARKER + "-1"), text.replace("com.android.launcher3/com.android.launcher3.uioverrides.QuickstepLauncher", "unknown", 1), text.replace("  taskId=42:", "  unknownTaskId=42:"), text.replace("\n\n" + MARKER, "\n" + text.splitlines()[2] + "\n\n" + MARKER)):
            with self.subTest(kind=len(bad)), self.assertRaises(ValueError): modeled_live_tasks(bad)

    def test_master_missing_disabled_unknown_and_wrong_original_pairs_are_refused(self):
        for master in ("null", "0", "2", "", "true"):
            with self.subTest(master=master), self.assertRaises(ValueError): modeled_restore((False, "null"), (True, "1"), armed=True, clicked=True, ui=True, master=master)
        with self.assertRaises(ValueError): modeled_restore((True, "0"), (True, "1"), armed=True, clicked=False, ui=True)

    def test_original_null_zero_and_one_are_exactly_restored_by_only_needed_ui_click(self):
        for original in ((False, "null"), (False, "0"), (True, "1")):
            state, deleted = modeled_restore(original, (True, "1"), armed=True, clicked=not original[0], ui=True)
            self.assertEqual(original, state); self.assertEqual(original[1] == "null", deleted)

    def test_unconfirmed_noop_arm_preserves_absence_without_delete(self):
        self.assertEqual(((False, "null"), False), modeled_restore((False, "null"), (False, "null"), armed=False, clicked=False, ui=False))

    def test_source_backed_partial_scalar_assignment_is_restored_by_settings_native_click(self):
        self.assertEqual(((False, "null"), True), modeled_restore((False, "null"), (False, "1"), armed=False, clicked=True, ui=True))

    def test_foreign_completed_arm_ui_only_native_acceptance_and_double_toggle_are_refused(self):
        for current, clicked, ui in (((False, "0"), False, False), ((True, "0"), True, True), ((False, "1"), True, False), ((True, "1"), False, True)):
            with self.subTest(current=current, clicked=clicked), self.assertRaises(ValueError): modeled_restore((False, "null"), current, armed=True, clicked=clicked, ui=ui)


class CameraSettingsUiSelectionAndCleanupModelTests(unittest.TestCase):
    def test_exact_installed_unique_same_row_switch_is_selected(self):
        self.assertEqual(1, modeled_selection(ui_fixture()))

    def test_duplicate_resources_text_switch_and_cross_row_nodes_are_refused(self):
        base = ui_fixture()
        variants = [base + [deepcopy(base[i])] for i in (2, 3, 4)]
        bad = deepcopy(base); bad[2]["id"] = "foreign:id/title"; variants.append(bad)
        bad = deepcopy(base); bad[3]["parent"] = 0; variants.append(bad)
        bad = deepcopy(base); bad[4]["id"] = "com.android.settings:id/foreignSwitch"; variants.append(bad)
        for bad in variants:
            with self.subTest(nodes=len(bad)), self.assertRaises(ValueError): modeled_selection(bad)

    def test_foreign_disabled_invisible_noncheckable_and_unactionable_nodes_are_refused(self):
        base = ui_fixture()
        for index, key, value in ((1,"package","foreign"),(4,"package","foreign"),(1,"enabled",False),(4,"visible",False),(4,"checkable",False),(4,"class","android.widget.CheckBox"),(1,"click_action",False)):
            bad = deepcopy(base); bad[index][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): modeled_selection(bad)

    def test_flags_restore_only_original_owned_union_with_exact_final_readback(self):
        self.assertEqual(1, modeled_flags(1, 1 | 2 | 16 | 64, actual=1))
        self.assertEqual(1, modeled_flags(1, 1, configured=False, actual=1))

    def test_foreign_unconfirmed_repeated_or_missing_flag_restoration_is_not_success(self):
        for kwargs in (dict(current=128, actual=1), dict(current=1 | 2 | 16 | 64, restoration_attempted=True, actual=1), dict(current=1 | 2 | 16 | 64, actual=None), dict(current=1 | 2 | 16 | 64, actual=2)):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): modeled_flags(1, **kwargs)

    def test_host_runtime_tokenizer_shell_model_preserves_uri_and_actual_status(self):
        # Host shell/tokenizer model only: not execution of Android Runtime/UiAutomation.
        uri = "intent:#Intent;action=" + ACTION + ";identifier=" + NONCE + ";launchFlags=0x18000000;component=com.android.settings/.Settings%24DevelopmentSettingsActivity;end"
        encoded = "printf '${FORMAT}' '" + uri + "'"
        encoded = encoded.replace("${FORMAT}", "%s\\n").replace(" ", "${IFS}")
        output = subprocess.run(("sh -c " + encoded + ";echo${IFS}" + MARKER + "-$?").split(), capture_output=True, text=True, check=True)
        self.assertEqual([uri, MARKER + "-0"], output.stdout.splitlines())
        output = subprocess.run(("sh -c nativecmpkit-no-such-modeled-command;echo${IFS}" + MARKER + "-$?").split(), capture_output=True, text=True, check=True)
        self.assertEqual([MARKER + "-127"], output.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
