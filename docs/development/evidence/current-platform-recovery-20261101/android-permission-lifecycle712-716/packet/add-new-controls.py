from pathlib import Path
p=Path('/root/nativecmpkit-worktrees/android-permission-lifecycle/scripts/ci/test_android_permission_lifecycle_source.py')
s=p.read_text().replace('import importlib.util\n','import importlib.util\nimport copy\nimport hashlib\nimport json\n')
needle='\n\nif __name__ == "__main__":\n'
assert s.count(needle)==1
new='''
    def test_new_complete_source_readback_and_receipt_refuse_missing_forged_native_inputs(self):
        c = contract()
        receipt = c.source_contract(ROOT)
        c.validate_source_receipt(receipt)
        self.assertEqual(set(c.SOURCE_FILES), set(receipt["source_inputs"]))
        self.assertEqual(len(c.SOURCE_FILES), len(set(c.SOURCE_FILES)))
        self.assertFalse(receipt["native_or_compile_success_inferred"])
        self.assertNotIn("AGENTS.md", receipt["source_inputs"])
        for name in ("library_tests.py", "android_device_tests.py", "workflow_matrix.py", "android_permission_lifecycle.py"):
            self.assertIn("scripts/ci/" + name, receipt["source_inputs"])
        for mutation in ("missing", "digest", "native", "wrong-api", "linked-claim"):
            with self.subTest(mutation=mutation):
                altered = copy.deepcopy(receipt)
                if mutation == "missing": altered["source_inputs"].pop(c.SOURCE)
                elif mutation == "digest": altered["source_inputs_sha256"] = "0" * 64
                elif mutation == "native": altered["native_or_compile_success_inferred"] = True
                elif mutation == "wrong-api": altered["verification_api_level"] = 34
                else: altered["extra"] = "not-the-exact-source-schema"
                with self.assertRaises(ValueError): c.validate_source_receipt(altered)

    def test_new_prepared_receipt_refuses_wrong_focus_api_certificate_source_and_runtime_grant(self):
        c = contract()
        inputs = dict.fromkeys(c.SOURCE_FILES, "1" * 64)
        bound = {"schema_version": 1, "source_inputs": inputs,
            "source_inputs_sha256": hashlib.sha256("".join(p + "\\0" + inputs[p] + "\\n" for p in sorted(inputs)).encode()).hexdigest(),
            "source_policy_verified": True, "verification_api_level": 35, "native_or_compile_success_inferred": False}
        focus = "android-permission-lifecycle-revoke-api35"
        inert = {"verification_api_level": 35, "focus": focus, "package": c.PACKAGE, "source_fixture": c.FIXTURE,
            "prepare_status": "passed", "recipient_installed": True, "automatic_runtime_permission_grant": False,
            "source_contract": bound, "source_apk_sha256": "2" * 64, "source_apk_bytes": 4096,
            "installed_readback": {"apk_sha256": "2" * 64, "exact_one_APK_path_observed": True},
            "apk_policy": {"compiled_manifest_inspected": True, "signature_control_only": True,
                "separate_uid_manifest": True, "five_runtime_permissions_only": True,
                "certificate_sha256": "3" * 64, "private_key_certificate_sha256": "3" * 64,
                "signature_verification_min_sdk_version": 35, "signature_verification_max_sdk_version": 35}}
        c.validate_prepared_receipt(inert, bound, 35, focus=focus)  # Inert validator boundary only, not a device receipt.
        changes = (("focus", "android-permission-location-api35"), ("verification_api_level", True),
            ("automatic_runtime_permission_grant", True), ("prepare_status", "failed"), ("recipient_installed", False),
            ("source_apk_bytes", False), ("source_apk_sha256", "4" * 64))
        for key, value in changes:
            with self.subTest(key=key):
                changed = copy.deepcopy(inert); changed[key] = value
                with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)
        for key, value in (("private_key_certificate_sha256", "4" * 64),
                           ("signature_verification_max_sdk_version", 34), ("separate_uid_manifest", False)):
            changed = copy.deepcopy(inert); changed["apk_policy"][key] = value
            with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)
        changed = copy.deepcopy(inert); changed["source_contract"]["source_inputs"][c.SOURCE] = "4" * 64
        with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)

    def test_new_request_refuses_boolean_old_api_wrong_module_broad_focus_and_unbound_plan(self):
        c = contract()
        for focus in FOCUSES:
            c.validate_request(35, (c.MODULE,), focus)
        for api, modules, focus in ((True, (c.MODULE,), next(iter(FOCUSES))), (34, (c.MODULE,), next(iter(FOCUSES))),
            (35, ("calf-io",), next(iter(FOCUSES))), (35, (c.MODULE, "calf-io"), next(iter(FOCUSES))),
            (35, (c.MODULE,), None), (35, (c.MODULE,), "android-permission-demo-contracts")):
            with self.assertRaises(ValueError): c.validate_request(api, modules, focus)
        bound = c.source_contract(ROOT)
        for focus in FOCUSES:
            plan = {"suite": "android-device", "explicit_test_focus": focus, "explicit_module_subset": [c.MODULE],
                "complete_suite_requested": False, "android_permission_lifecycle": {"package": c.PACKAGE,
                    "source_fixture": c.FIXTURE, "verification_api_level": 35, "source_contract": bound}}
            c.validate_plan(plan)
            altered = copy.deepcopy(plan); altered["explicit_module_subset"] = ["calf-io", c.MODULE]
            with self.assertRaises(ValueError): c.validate_plan(altered)
            altered = copy.deepcopy(plan); altered["explicit_test_focus"] = "android-permission-demo-contracts"
            with self.assertRaises(ValueError): c.validate_plan(altered)

    def test_new_own_metadata_parser_never_expands_accepted_whitelist_or_allows_split_paths(self):
        c = contract()
        metadata = {"artifactType": {"type": "APK"}, "applicationId": c.PACKAGE, "variantName": "debug",
            "elements": [{"type": "SINGLE", "filters": [], "outputFile": "app-debug.apk"}]}
        self.assertEqual("app-debug.apk", c.validate_metadata(json.dumps(metadata).encode()))
        for mutation in ("package", "variant", "split", "path", "duplicate", "nonfinite"):
            changed = copy.deepcopy(metadata)
            if mutation == "package": changed["applicationId"] = "foreign.test"
            elif mutation == "variant": changed["variantName"] = "release"
            elif mutation == "split": changed["elements"].append(dict(changed["elements"][0]))
            elif mutation == "path": changed["elements"][0]["outputFile"] = "../foreign.apk"
            payload = (b'{"artifactType":{},"artifactType":{}}' if mutation == "duplicate" else
                       b'{"artifactType":NaN}' if mutation == "nonfinite" else json.dumps(changed).encode())
            with self.assertRaises(ValueError): c.validate_metadata(payload)
        controller = source(CI / "android_permission_lifecycle.py")
        self.assertIn("def metadata_apk(self)", controller)
        self.assertNotIn("from android_geo_probe import metadata_apk", controller)
        self.assertNotIn(c.FIXTURE, source(CI / "android_geo_probe.py"))

    def test_new_reporter_permission_exception_is_exact_signature_only_not_native_grant(self):
        c = contract()
        payload = (ROOT / c.MODULE / "src/androidDeviceTest/AndroidManifest.xml").read_bytes()
        c.validate_reporter_source(payload)
        for permission in ("android.permission.ACCESS_FINE_LOCATION", "android.permission.POST_NOTIFICATIONS",
                           c.PACKAGE + ".ARBITRARY_CONTROL"):
            manifest = ET.fromstring(payload)
            ET.SubElement(manifest, "uses-permission", {ANDROID + "name": permission})
            with self.assertRaises(ValueError): c.validate_reporter_source(ET.tostring(manifest))
        storage = source(CI / "android_storage_probe.py")
        self.assertIn('PERMISSION_LIFECYCLE_CONTROL = "' + c.PERMISSION + '"', storage)
        self.assertIn("allowed = {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL,", storage)
        self.assertIn("set(requested) <= {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL}", storage)
        self.assertIn('"Reporter cannot bypass another UID\\'s native storage or SAF grant"', storage)

    def test_new_command_receipt_gates_and_actual_api_source_rechecks_preserve_assembly(self):
        text = source(CI / "library_tests.py")
        tree = ast.parse(text)
        command = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "gradle_command")
        body = ast.get_source_segment(text, command)
        self.assertIn("android_permission_lifecycle_receipt is not None and (not lifecycle_required or for_assembly)", body)
        self.assertIn("if lifecycle_required:", body)
        self.assertIn("if lifecycle_required and not for_assembly:", body)
        self.assertIn("permission_lifecycle.validate_prepared_receipt", body)
        self.assertIn('focus=test_plan["explicit_test_focus"]', body)
        self.assertIn('permission_lifecycle.source_contract(root) != test_plan["android_permission_lifecycle"]["source_contract"]', body)
        self.assertEqual(1, body.count("nativecmpkitOwnedPermissionLifecycle=true"))
        self.assertEqual(1, body.count("nativecmpkitPermissionLifecycleFocus="))
        run = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"))
        self.assertIn("android_permission_lifecycle_required(test_plan) and android_user_home is None", run)
        self.assertIn('if actual_api != "35":', run)
        self.assertIn('receipt["android_permission_lifecycle"] = dict(android_permission_lifecycle_receipt)', run)

    def test_new_direct_controller_route_checks_precede_sdk_output_host_and_owner_mutation(self):
        text = source(CI / "android_device_tests.py")
        tree = ast.parse(text)
        body = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run"))
        self.assertLess(body.index("validate_api_selection(api_level, only_modules, focus)"), body.index("output = "))
        run = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"))
        self.assertLess(run.index("validate_api_selection(api_level, only_modules, focus)"), run.index("require_host()"))
        self.assertLess(run.index("focus in permission_lifecycle_contract.FOCUSES"), run.index("require_host()"))
        self.assertIn("permission_lifecycle_contract.validate_request(api_level, modules, focus)", text)
        self.assertIn('mkdir(mode=0o700 if permission_lifecycle_required else 0o777)', text)
        self.assertIn('environment=env, api_level=api_level, focus=focus)', text)
        self.assertIn('result["permission_lifecycle_source_unchanged_after_cleanup"] = (', text)
        self.assertIn('result["permission_lifecycle"].get("prepare_status")', text) if False else None
        self.assertIn('result.get("permission_lifecycle", {}).get("prepare_status") == "passed"', text)
        self.assertIn('result["permission_lifecycle"].get("cleanup_status") == "passed"', text)
        self.assertIn('result["permission_lifecycle"].get("owned_recipient_removed") is True', text)
        self.assertIn('or permission_lifecycle is not None or storage_probe is not None', text)

    def test_new_back_stability_and_teardown_keep_native_failure_and_all_owned_cleanup(self):
        ui = source(KT / "PermissionLifecycleSystemUi.kt")
        self.assertIn("automation.waitForIdle(250, minOf(4000L, remaining))", ui)
        self.assertLess(ui.index("performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK)"), ui.index("automation.waitForIdle"))
        bridge = source(KT / "OwnedPermissionLifecycle.kt")
        self.assertIn('assertNull(binder, "A replacement lifecycle Binder cannot be admitted")', bridge)
        self.assertIn("if (activityGeneration == null) activityGeneration = activeGeneration else assertEquals(activityGeneration, activeGeneration)", bridge)
        self.assertIn('assertNull(protocolError, "A lifecycle protocol/death failure cannot pass as clean native disposal")', bridge)
        for text in (bridge, source(KT / "AndroidPermissionLifecycleDeviceTest.kt")):
            self.assertIn("addSuppressed(error)", text)
            self.assertIn("failure?.let { throw it }", text)

    def test_new_disposable_build_is_public_source_dependency_only_and_never_publication(self):
        build = source(FIXTURE / "build.gradle.kts")
        settings = source(FIXTURE / "settings.gradle.kts")
        self.assertIn("minSdk = 35", build)
        self.assertIn("targetSdk = 37", build)
        self.assertIn('versionName = "verification-only-api35-permission-lifecycle"', build)
        for module in ("core", "location", "background-location", "camera", "notifications"):
            self.assertIn('implementation("verification.nativecmpkit:unpublished-permission-' + module + '")', build)
            self.assertIn('project(":calf-permissions:calf-permissions-' + module + '")', settings)
        self.assertNotIn("module.publication", build)
        self.assertNotIn("maven-publish", build)
        self.assertNotIn("calf-sample", settings)
        workflow = source(ROOT / ".github/workflows/gradle.yml")
        self.assertIn("build/ci-verification/${{ matrix.slot }}/permission-lifecycle/receipt.json", workflow)
'''
s=s.replace(needle,'\n'+new+needle)
s=s.replace('        self.assertIn(\'result["permission_lifecycle"].get("prepare_status")\', text) if False else None\n','')
p.write_text(s)
print('Added 9 genuinely NEW pure/read-only source controls; no test execution yet.')
