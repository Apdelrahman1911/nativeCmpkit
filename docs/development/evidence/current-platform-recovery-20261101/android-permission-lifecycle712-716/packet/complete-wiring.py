from pathlib import Path
R=Path('/root/nativecmpkit-worktrees/android-permission-lifecycle')
def edit(rel, old, new):
    p=R/rel; s=p.read_text(); assert s.count(old)==1,(rel,s.count(old),old[:100]); p.write_text(s.replace(old,new))
L='scripts/ci/library_tests.py'
edit(L,'''    if android_permission_demo_required(result):
        if focus in permission_lifecycle.FOCUSES:
            result["android_permission_lifecycle"] = {"package": permission_lifecycle.PACKAGE,
                "source_fixture": permission_lifecycle.FIXTURE, "verification_api_level": permission_lifecycle.API,
                "source_contract": permission_lifecycle.source_contract(root)}
        else:
            import android_permission_demo
            result["android_permission_demo"] = {"package": android_permission_demo.PACKAGE,
                "source_fixture": android_permission_demo.FIXTURE, "source_contract": android_permission_demo.source_contract(root)}
''','''    if android_permission_lifecycle_required(result):
        result["android_permission_lifecycle"] = {"package": permission_lifecycle.PACKAGE,
            "source_fixture": permission_lifecycle.FIXTURE, "verification_api_level": permission_lifecycle.API,
            "source_contract": permission_lifecycle.source_contract(root)}
    elif android_permission_demo_required(result):
        import android_permission_demo
        result["android_permission_demo"] = {"package": android_permission_demo.PACKAGE,
            "source_fixture": android_permission_demo.FIXTURE, "source_contract": android_permission_demo.source_contract(root)}
''')
edit(L,'''                   android_permission_demo_receipt: dict | None = None,
                   for_assembly:''','''                   android_permission_demo_receipt: dict | None = None,
                   android_permission_lifecycle_receipt: dict | None = None,
                   for_assembly:''')
edit(L,'''    permission_required = android_permission_demo_required(test_plan)
''','''    lifecycle_required = android_permission_lifecycle_required(test_plan)
    if android_permission_lifecycle_receipt is not None and (not lifecycle_required or for_assembly):
        raise ValueError("No lifecycle prepared receipt on unrelated/default/assembly-only commands")
    if lifecycle_required:
        if permission_lifecycle.source_contract(root) != test_plan["android_permission_lifecycle"]["source_contract"]:
            raise ValueError("Permission lifecycle current source identities changed before the owning command")
        if not for_assembly:
            permission_lifecycle.validate_prepared_receipt(android_permission_lifecycle_receipt,
                test_plan["android_permission_lifecycle"]["source_contract"])
    permission_required = android_permission_demo_required(test_plan)
''')
edit(L,'''        if permission_required and not for_assembly:
            command.append("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedPermissionDemo=true")
''','''        if lifecycle_required and not for_assembly:
            command.extend(["-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedPermissionLifecycle=true",
                            "-Pandroid.testInstrumentationRunnerArguments.nativecmpkitPermissionLifecycleFocus=" + test_plan["explicit_test_focus"]])
        if permission_required and not for_assembly:
            command.append("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedPermissionDemo=true")
''')
edit(L,'''        android_permission_demo_receipt: dict | None = None, android_storage_probe_receipt: dict | None = None) -> dict:
''','''        android_permission_demo_receipt: dict | None = None, android_storage_probe_receipt: dict | None = None,
        android_permission_lifecycle_receipt: dict | None = None) -> dict:
''')
edit(L,'''    if android_permission_demo_required(test_plan) and android_user_home is None:
''','''    if android_permission_lifecycle_required(test_plan) and android_user_home is None:
        raise ValueError("Permission lifecycle instrumentation requires the controller's same existing private signing home")
    if android_permission_demo_required(test_plan) and android_user_home is None:
''')
edit(L,'''                             android_permission_demo_receipt=android_permission_demo_receipt,
''','''                             android_permission_demo_receipt=android_permission_demo_receipt,
                             android_permission_lifecycle_receipt=android_permission_lifecycle_receipt,
''')
edit(L,'''        if android_permission_demo_required(test_plan):
            import android_permission_demo
            actual_api = context["android_emulator"]["api_level"]
''','''        if android_permission_lifecycle_required(test_plan):
            actual_api = context.get("android_emulator", {}).get("api_level")
            if actual_api != "35":
                raise ValueError("Permission lifecycle native execution requires actual API35")
            permission_lifecycle.validate_prepared_receipt(android_permission_lifecycle_receipt,
                test_plan["android_permission_lifecycle"]["source_contract"], int(actual_api))
            if permission_lifecycle.source_contract(root) != test_plan["android_permission_lifecycle"]["source_contract"]:
                raise ValueError("Permission lifecycle source map changed before native execution")
        if android_permission_demo_required(test_plan):
            import android_permission_demo
            actual_api = context["android_emulator"]["api_level"]
''')
edit(L,'''        if android_permission_demo_required(test_plan):
            receipt["android_permission_demo"] = dict(android_permission_demo_receipt)
''','''        if android_permission_lifecycle_required(test_plan):
            receipt["android_permission_lifecycle"] = dict(android_permission_lifecycle_receipt)
        if android_permission_demo_required(test_plan):
            receipt["android_permission_demo"] = dict(android_permission_demo_receipt)
''')
D='scripts/ci/android_device_tests.py'
edit(D,'import android_permission_demo\n','import android_permission_demo\nimport android_permission_lifecycle\nimport android_permission_lifecycle_contract as permission_lifecycle_contract\n')
edit(D,'"android_permission_demo.py", "android_storage_probe.py",','"android_permission_demo.py", "android_permission_lifecycle.py", "android_permission_lifecycle_contract.py", "android_storage_probe.py",')
edit(D,'    if focus in lt.ANDROID_IO_REMOTE_FOCUSES:\n        validate_api_selection(api_level, only_modules, focus)  # Even direct owning-controller calls cannot expand the remote route.\n','    if focus in lt.ANDROID_IO_REMOTE_FOCUSES or focus in permission_lifecycle_contract.FOCUSES:\n        validate_api_selection(api_level, only_modules, focus)  # Direct calls cannot expand the remote or lifecycle route.\n')
edit(D,'    permission_demo_required = lt.android_permission_demo_required(plan)\n','    permission_demo_required = lt.android_permission_demo_required(plan)\n    permission_lifecycle_required = lt.android_permission_lifecycle_required(plan)\n')
edit(D,' or permission_demo_required or storage_required or remote_documents_required\n',' or permission_demo_required or permission_lifecycle_required or storage_required or remote_documents_required\n')
edit(D,'        (output / "android-user").mkdir()\n','        (output / "android-user").mkdir(mode=0o700 if permission_lifecycle_required else 0o777)\n')
edit(D,'    if io_documents_required or permission_demo_required or storage_required or remote_documents_required:\n','    if io_documents_required or permission_demo_required or permission_lifecycle_required or storage_required or remote_documents_required:\n')
edit(D,'    permission_demo = None\n','    permission_demo = None\n    permission_lifecycle = None\n')
edit(D,'    if permission_demo_required:\n        result["reporter_compile_deferred_until_permission_demo_identity"] = True\n','    if permission_demo_required:\n        result["reporter_compile_deferred_until_permission_demo_identity"] = True\n    if permission_lifecycle_required:\n        result["reporter_compile_deferred_until_permission_lifecycle_identity"] = True\n')
edit(D,'        if deferred_api23_assembly or io_documents_required or permission_demo_required or storage_required or remote_documents_required or camera_developer_required:\n','        if deferred_api23_assembly or io_documents_required or permission_demo_required or permission_lifecycle_required or storage_required or remote_documents_required or camera_developer_required:\n')
edit(D,'        if permission_demo_required:\n            permission_demo = android_permission_demo.OwnedPermissionDemo','''        if permission_lifecycle_required:
            # Keep the owner before prepare: failed source/APK/signature/install still enters identity-safe close.
            permission_lifecycle = android_permission_lifecycle.OwnedPermissionLifecycle(root, output, home, SERIAL,
                lambda: process.poll() is None and avd_name(home) == name, environment=env, api_level=api_level)
            result["permission_lifecycle"] = permission_lifecycle.prepare()
            permission_lifecycle_contract.validate_prepared_receipt(result["permission_lifecycle"],
                plan["android_permission_lifecycle"]["source_contract"], api_level)
            execution = lt.execute(root, assemble, output / "apk-assembly.log", 900, RESERVE_MIB, env=env)
            result["setup_stages"]["apk-assembly"] = execution
            if execution["exit_code"] != 0 or execution.get("stop_reason"):
                raise RuntimeError("Reporter setup failed before any permission lifecycle native execution")
            if permission_lifecycle_contract.source_contract(root) != plan["android_permission_lifecycle"]["source_contract"]:
                raise ValueError("Permission lifecycle source map changed during reporter compilation")
        if permission_demo_required:
            permission_demo = android_permission_demo.OwnedPermissionDemo''')
edit(D,'                         **({"android_permission_demo_receipt": dict(permission_demo.receipt)} if permission_demo is not None else {}),\n','                         **({"android_permission_demo_receipt": dict(permission_demo.receipt)} if permission_demo is not None else {}),\n                         **({"android_permission_lifecycle_receipt": dict(permission_lifecycle.receipt)} if permission_lifecycle is not None else {}),\n')
edit(D,'                if permission_demo is not None:\n                    try:\n                        result["permission_demo"] = permission_demo.close()\n','''                if permission_lifecycle is not None:
                    try:
                        result["permission_lifecycle"] = permission_lifecycle.close()
                    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
                        result["permission_lifecycle"] = dict(permission_lifecycle.receipt) | {
                            "cleanup_status": "failed", "owned_recipient_removed": False, "cleanup_error": type(error).__name__}
                        result["permission_lifecycle_cleanup_error_origin"] = preflight_error_origin(error)
                if permission_demo is not None:
                    try:
                        result["permission_demo"] = permission_demo.close()
''')
edit(D,'or permission_demo is not None or storage_probe is not None) and verified and\n','or permission_demo is not None or permission_lifecycle is not None or storage_probe is not None) and verified and\n')
edit(D,'        if remote_documents_required:\n            try:\n                result["remote_source_unchanged_after_cleanup"] = (\n','''        if permission_lifecycle_required:
            try:
                result["permission_lifecycle_source_unchanged_after_cleanup"] = (
                    permission_lifecycle_contract.source_contract(root) == plan["android_permission_lifecycle"]["source_contract"])
            except (OSError, ValueError, UnicodeError):
                result["permission_lifecycle_source_unchanged_after_cleanup"] = False
        if remote_documents_required:
            try:
                result["remote_source_unchanged_after_cleanup"] = (
''')
edit(D,'                            (not permission_demo_required or (result.get("permission_demo", {}).get("prepare_status") == "passed" and\n','''                            (not permission_lifecycle_required or (result.get("permission_lifecycle_source_unchanged_after_cleanup") is True and
                             result.get("permission_lifecycle", {}).get("prepare_status") == "passed" and
                             result["permission_lifecycle"].get("cleanup_status") == "passed" and
                             result["permission_lifecycle"].get("owned_recipient_removed") is True and
                             not result["permission_lifecycle"].get("prepare_error") and not result["permission_lifecycle"].get("cleanup_error"))) and
                            (not permission_demo_required or (result.get("permission_demo", {}).get("prepare_status") == "passed" and
''')
edit(D,'    if focus in lt.ANDROID_IO_REMOTE_FOCUSES:\n        if type(api_level) is not int or api_level != 35 or modules != ("calf-io",):\n','''    if focus in permission_lifecycle_contract.FOCUSES:
        if type(api_level) is not int or api_level != 35 or modules != (permission_lifecycle_contract.MODULE,):
            raise ValueError("Permission lifecycle requires exact integer API35, one finite focus and permission core only")
        return
    if focus in lt.ANDROID_IO_REMOTE_FOCUSES:
        if type(api_level) is not int or api_level != 35 or modules != ("calf-io",):
''')
edit(D,'    if focus == lt.camera_callback.FOCUS:\n        lt.plan(root, "android-device", only_modules=only_modules, focus=focus)\n','    if focus == lt.camera_callback.FOCUS or focus in permission_lifecycle_contract.FOCUSES:\n        lt.plan(root, "android-device", only_modules=only_modules, focus=focus)\n')
M='scripts/ci/workflow_matrix.py'
edit(M,'import android_storage_compatibility_plan as storage_plan\n','import android_storage_compatibility_plan as storage_plan\nimport android_permission_lifecycle_contract as permission_lifecycle\n')
for mapping,val in [('PROFILES','("android-device-api35",)'),('MODULE_SUBSETS','"calf-permissions/core"')]:
    edit(M,mapping+' = {\n',mapping+' = {\n'+''.join(f'    "{focus}": {val},\n' for focus in ['android-permission-location-api35','android-permission-lifecycle-grant-api35','android-permission-lifecycle-revoke-api35']))
edit(M,'    if profile == "android-permission-demo":\n        for row in rows:\n','''    if profile in permission_lifecycle.FOCUSES:
        if len(rows) != 1 or rows[0]["slot"] != "android-device-api35" or MODULE_SUBSETS[profile] != permission_lifecycle.MODULE:
            raise ValueError("Permission lifecycle refuses broad or default matrix routing")
        rows[0].update(**{"emulator-api": "35", "test-focus": profile})
    if profile == "android-permission-demo":
        for row in rows:
''')
S='scripts/ci/android_storage_probe.py'
edit(S,'PERMISSION_DEMO_BIND = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO"\n','PERMISSION_DEMO_BIND = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO"\nPERMISSION_LIFECYCLE_CONTROL = "io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle.CONTROL_LIFECYCLE"\n')
edit(S,'    allowed = {PERMISSION, PERMISSION_DEMO_BIND, "android.permission.INTERNET",','    allowed = {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL, "android.permission.INTERNET",')
edit(S,'set(requested) <= {PERMISSION, PERMISSION_DEMO_BIND} and not reporter.findall','set(requested) <= {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL} and not reporter.findall')
P='calf-permissions/core/src/androidDeviceTest/AndroidManifest.xml'
edit(P,'    <uses-permission android:name="io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO" />\n','    <uses-permission android:name="io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO" />\n    <uses-permission android:name="io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle.CONTROL_LIFECYCLE" />\n')
edit(P,'    <queries>\n','    <queries>\n        <package android:name="io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle" />\n        <package android:name="com.android.settings" />\n')
W='.github/workflows/gradle.yml'
edit(W,'android-permission-demo, android-permission-demo-call-denial-recovery,','android-permission-location-api35, android-permission-lifecycle-grant-api35, android-permission-lifecycle-revoke-api35, android-permission-demo, android-permission-demo-call-denial-recovery,')
edit(W,"|| inputs.profile == 'android-permission-demo' &&", "|| (inputs.profile == 'android-permission-location-api35' || inputs.profile == 'android-permission-lifecycle-grant-api35' || inputs.profile == 'android-permission-lifecycle-revoke-api35') && 'cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64' || inputs.profile == 'android-permission-demo' &&")
edit(W,'            build/ci-verification/${{ matrix.slot }}/storage-probe/receipt.json\n','            build/ci-verification/${{ matrix.slot }}/storage-probe/receipt.json\n            build/ci-verification/${{ matrix.slot }}/permission-lifecycle/receipt.json\n')
print('Wiring applied; no planner/controller/compiler/native/Git execution.')
