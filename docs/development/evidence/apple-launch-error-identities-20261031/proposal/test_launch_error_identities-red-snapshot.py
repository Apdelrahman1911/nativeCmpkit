"""Private modeled diagnostic checks; zero Apple or profiling executions."""
import json
import subprocess
import unittest

import apple_launch_diagnostics as subject

BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
DEVICE = "11111111-1111-1111-1111-111111111111"
START = "2026-10-30T10:09:26+00:00"
END = "2026-10-30T10:10:04+00:00"
NESTED = ('Error Domain=FBSOpenApplicationServiceErrorDomain Code=1 "refused" '
          'UserInfo={NSUnderlyingError=Error Domain=RBSRequestErrorDomain Code=5 '
          'UserInfo={NSUnderlyingError=Error Domain=NSPOSIXErrorDomain Code=13 "private reason"}}')
EXPECTED = [{"domain": "FBSOpenApplicationServiceErrorDomain", "code": 1},
            {"domain": "NSPOSIXErrorDomain", "code": 13},
            {"domain": "RBSRequestErrorDomain", "code": 5}]


class LaunchErrorIdentityTests(unittest.TestCase):
    def row(self, message=NESTED, **changes):
        return {"timestamp": "2026-10-30 10:09:30.100000+0000",
                "processImagePath": "/private/synthetic/system/SpringBoard",
                "eventMessage": BUNDLE + " " + message, **changes}

    def summarize(self, rows):
        return subject.summarize(json.dumps(rows).encode(), BUNDLE, START, END)

    def test_owned_nested_errors_retain_domain_code_observations_without_a_causal_claim(self):
        result = self.summarize([self.row()])
        self.assertEqual(EXPECTED, result["observed_error_identities"])
        self.assertFalse(result["root_cause_proven"])
        self.assertFalse(result["native_functionality_verified"])
        self.assertFalse(result["raw_messages_paths_or_log_uploaded"])

    def test_simctl_and_nserror_forms_deduplicate_the_same_observation(self):
        result = self.summarize([self.row('(domain=NSPOSIXErrorDomain, code=13) '
                                         'Error Domain=NSPOSIXErrorDomain Code=13 "private"')])
        self.assertEqual([{"domain": "NSPOSIXErrorDomain", "code": 13}], result["observed_error_identities"])

    def test_foreign_bundle_prefix_process_and_time_cannot_supply_error_identities(self):
        rows = [self.row(eventMessage=BUNDLE + "foreign " + NESTED),
                self.row(eventMessage="foreign.bundle " + NESTED),
                self.row(processImagePath="/private/synthetic/UnrelatedApplication"),
                self.row(timestamp="2026-10-30T10:08:00+00:00")]
        result = self.summarize(rows)
        self.assertEqual([], result["observed_error_identities"])
        self.assertEqual(0, result["owned_system_rows"])

    def test_unknown_domains_suffixes_and_malformed_codes_never_leak_or_partially_match(self):
        for message in ('Error Domain=UNIQUE_PRIVATE_ERROR_DOMAIN Code=7',
                        'Error Domain=NSPOSIXErrorDomainPRIVATE Code=13',
                        'Error Domain=NSPOSIXErrorDomain Code=13PRIVATE',
                        'Error Domain=NSPOSIXErrorDomain Code=100000000000',
                        '(domain=NSPOSIXErrorDomain, code=13PRIVATE)'):
            with self.subTest(message=message):
                result = self.summarize([self.row(message)])
                self.assertEqual([], result["observed_error_identities"])
                self.assertNotIn("UNIQUE_PRIVATE_ERROR_DOMAIN", json.dumps(result))

    def test_private_reasons_symbols_paths_and_addresses_are_never_serialized(self):
        private = "UNIQUE_PRIVATE_REASON /private/user/PRIVATE_FILE UNKNOWN_PRIVATE_SYMBOL 0xabcdef"
        result = self.summarize([self.row(NESTED + " " + private)])
        self.assertEqual(EXPECTED, result["observed_error_identities"])
        for canary in private.split():
            self.assertNotIn(canary, json.dumps(result))
        self.assertNotIn("private reason", json.dumps(result))

    def test_identity_count_and_numeric_bounds_fail_closed(self):
        with self.assertRaises(ValueError):
            self.summarize([self.row("Error Domain=NSPOSIXErrorDomain Code=2147483648")])
        with self.assertRaises(ValueError):
            self.summarize([self.row("Error Domain=NSPOSIXErrorDomain Code=" + str(n)) for n in range(17)])
        result = self.summarize([self.row("Error Domain=NSOSStatusErrorDomain Code=-2147483648")])
        self.assertEqual([{"domain": "NSOSStatusErrorDomain", "code": -2147483648}],
                         result["observed_error_identities"])

    def test_collection_uses_the_same_single_owned_query_with_no_launch_retry(self):
        commands = []
        def control(command, timeout):
            commands.append((command, timeout))
            return subprocess.CompletedProcess(command, 0, json.dumps([self.row()]).encode(), b"")
        result = subject.collect(DEVICE, BUNDLE, START, END, control)
        self.assertEqual(EXPECTED, result["observed_error_identities"])
        self.assertEqual(1, len(commands))
        command, timeout = commands[0]
        self.assertEqual(["/usr/bin/xcrun", "simctl", "spawn", DEVICE, "log", "show"], command[:6])
        self.assertEqual('eventMessage CONTAINS "' + BUNDLE + '"', command[-1])
        self.assertEqual(30, timeout)
        self.assertNotIn("launch", command)

    def test_nonzero_query_cannot_supply_error_identities_or_a_diagnostic_pass(self):
        def control(command, timeout):
            return subprocess.CompletedProcess(command, 1, json.dumps([self.row()]).encode(), b"PRIVATE_FAILURE")
        result = subject.collect(DEVICE, BUNDLE, START, END, control)
        self.assertEqual("unavailable", result["status"])
        self.assertEqual([], result.get("observed_error_identities", []))
        self.assertFalse(result["native_functionality_verified"])
        self.assertFalse(result["root_cause_proven"])
        self.assertNotIn("PRIVATE_FAILURE", json.dumps(result))

    def test_actual_python_caller_keeps_nested_diagnostic_failure_and_owned_cleanup(self):
        # Reuse only a modeled ownership fixture, not an accepted native method.
        import test_ios_ui_application as fixture_module
        app = fixture_module.a
        fixture = fixture_module.OwnedApplicationTests(
            methodName="test_only_finite_pre_pid_profile_refusal_queries_owned_log_and_keeps_failure_cleanup")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        def control(command, timeout=90):
            actual = fixture.launch_diagnostic_control(command, timeout)
            if command[:6] == ["/usr/bin/xcrun", "simctl", "spawn", DEVICE, "log", "show"]:
                bundle = command[-1].split('"')[1]
                rows = [self.row(eventMessage=bundle + " denied by service delegate " + NESTED)]
                return subprocess.CompletedProcess(command, 0, json.dumps(rows).encode(), b"")
            return actual
        focus = app.lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS
        arguments = [*sorted(app.TEST_ARGUMENTS), "--ktest_gradle_filter=" + app.lt.ui_application_focus_filter(focus)]
        result = fixture.fixture_run(control=control, launch=fixture.failed_profile_launch(),
                                     arguments=arguments, image_diagnostics="darwin-tools")
        self.assertEqual(EXPECTED, result["owned_launch_diagnostics"]["observed_error_identities"])
        self.assertFalse(result["transport_passed"])
        self.assertFalse(result["image_memory_profile"]["profile_passed"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
        self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
        self.assertEqual(1, sum("show" in command for command in fixture.commands))
        self.assertEqual(1, sum("launch" in command for command in fixture.commands))
