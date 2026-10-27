# Report-contract repair and cache-security regressions — 2026-10-27

Work remains single-agent on `development/preview-hardening`. Actions verification
is authorized with all actions allowed and no mandatory SHA pinning. Publishing,
releases and deployments remain gated; `main` and imported history are preserved.
No finding is closed by this checkpoint.

## Android's first hosted device attempt failed before tests

Run [40422019219](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40422019219)
at immutable `d849515b2a1f6048ed280e44e677f532a57d4f5f` failed. Tooling and APK
assembly succeeded (264.08 seconds; 163 tasks, 154 executed / 9 cached). The owned
API35/x86_64 emulator booted with SELinux Enforcing and shut down cleanly, exit0,
without forced process-group termination. **Zero library tests and XML reports**
were produced: all three connected tasks hit the init script's report-path guard.
The [independent ZIP/Git/receipt review](evidence/github-actions/40422019219/lead-independent-review.json)
verifies this failure, not successful native behavior.

The [executed AGP9.4.0 getter inspection](evidence/android-report-contract-20261027-001/receipt.json)
establishes two distinct paths for IO, picker and WebView:

- `getXmlResultsDirectory()`:
  `build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest`
- `getResultsDir()` (UTP/protobuf output):
  `build/outputs/androidTest-results/connected/androidMain`

The earlier runner conflated them. Its plan and guarded XML collector now use the
actual intermediate tree, retain an independent UTP-output guard, and record both
relative paths. New regressions ensure old UTP or Android-host XML cannot satisfy
missing native results. The executed inspection ran no connected tests. The
source repair still requires a new immutable hosted device execution.

## Actual cache red; Windows equivalence is not assumed

The [held-source Linux/JDK17 execution](evidence/native-cache-tests/red-20261027-003/receipt.json)
compiled the **actual** picker/share cache production and test sources with
Kotlin2.4.20/JUnit4 and real cached dependencies, without stubs. All702 selected
inputs stayed unchanged. It executed19 methods: **18 passed / 1 failed**, zero
skips. Share's `foreignWritableCacheIsRejectedWithoutRepairingItsPermissions`
reproduces silent chmod-and-trust of an already foreign-writable cache. Existing
bytes, unchanged reuse and concurrent writers were actually tested; this is not
JNI loading, Gradle packaging or Windows execution.

Three earlier setup attempts remain archived separately: the PowerShell string's
Kotlin interpolation compile error, disk-reserve refusal, and Java runner's
ambiguous `Result` import. They executed **zero tests** and were corrected in the
fixtures/driver, not counted as defect reproductions or successes.

Windows test fixtures no longer skip POSIX-only scenarios. They exercise actual
Windows ACL grants/readback, actual file symlinks and a directory junction whose
JDK attributes are `isOther=true` / `isSymbolicLink=false`. Unsupported security
operations fail rather than skip. Production ownership/ACL/reparse repairs and
an immutable Windows red/green execution are still required.

## Efficient targeted verification and unchanged issue state

Fixed finite profiles now include `ios` (iPhone only, no repeated successful macOS
desktop), `ios-ui` (`calf-ui` only), and `windows-cache` (picker/share only).
Subset discovery and execution receive identical source-defined modules; receipts
explicitly mark incomplete coverage. The full matrix still has eleven slots;
diagnostic subsets cannot become full-platform or release certification.

The [held-source preflight](evidence/ci-preflight-20261027-001/lead-review.json)
passed all21 commands:806 actual Python tooling methods, including126 CI methods,
strict MkDocs and actionlint on both actual workflows. All13,569 Git-listed inputs
stayed unchanged during the check and before archive. These are tooling fixtures,
not Windows/Android/iOS or packaged-consumer executions; the19 Linux library
cache tests above are separate. This paragraph/archive are additive after that
dirty-source check, not a circular immutable-candidate certification.

The [six progress comments](evidence/issue-progress-d849515b/progress-receipts.json)
were read back successfully without changing issue bodies, labels or states.
All164 dispositions remain89 implemented / 67 partially verified / 8 unresolved /
**0 verified**. Android, UIKit, Windows ACL/reparse, dependency/native payload,
legal, ABI/minimum-platform and strict packaged-consumer gates remain open.

The additive archive newline/whitespace rule preserves development evidence's
hashed bytes, matching existing migration/testing archive rules. It does not
exclude production sources; the earlier staged-log whitespace failure remains.
The [owned-output cleanup](evidence/owned-output-cleanup-20261027-001.json)
removed only two prior nativeCmpkit-generated static documentation sites after
recording their file hashes. Source, logs, reports, dependencies, caches and
other projects were not removed. Heavy local builds retain the8GiB reserve.

## Additive third Android failure and truthful native-host scope

The owner reaffirmed single-agent containment on2026-10-27; no historical agent
was resumed. Autonomous read-only verification remains authorized and publishing,
release and Pages gates are unchanged.

Run [40430738675](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40430738675)
at immutable `fa27c39fc307b51354d98e0a54a7f6e64e60c4fc` passes tooling, APK
assembly and all three child-selector/XML/UTP/task-marker guards. Connected
execution fails135.05s later with **zero XML / zero testcase evidence**. Actual
API35/x86_64/SELinux Enforcing boot and clean exit0 teardown are reviewed.
The [independent artifact/Git/receipt review](evidence/github-actions/40430738675/lead-independent-review.json)
confirms all702 committed inputs unchanged. The last bounded job tail now shows
AGP's generic `There were failing tests` at its actual line456, but not the
underlying UTP/device cause. Do not infer executed tests or a production fix.

The [owning early-diagnostics repair](android-device-selection.md#owning-diagnostic-repair-not-a-native-fix)
retains bounded connected-task/cause excerpts and inert XML/UTP hashes instead
of uploading complete logs, protobufs or binaries. Eleven new collector methods
and one source guard bring local CI fixtures to144 passing methods; these
synthetic checks run no Android library tests. An immutable diagnostic rerun is
still required; preserve the failed third run alongside earlier failures.

The [actual native-entry diagnostic](native-ui-application-host.md) compiles and
runs Linux Kotlin/Native2.4.20 custom entries under three runner flags. Six
repeated generated fixture executions/two methods pass, **zero library/iOS
tests**. The Worker registers the suite but bodies run on main. Worker body and
failure propagation, genuine UIKit application hosting and simulator/native
presentation remain unverified. Compose v2's Skiko scene is not an application
host; the helper comment now says so instead of overstating evidence. Preserve
the earlier disk-guard/download/driver failure, not only the later probe pass.

The [three additional issue comments](evidence/issue-progress-fa27c39f/receipt.json)
on IO-022/#149, NATIVE-031/#86 and BUILD-007/#40 were exact-readback verified;
bodies/titles/labels/states are unchanged. Installed-CLI pagination failures
occurred before POST and remain archived. Ledger stays88 implemented /68
partially verified /8 unresolved /**0 verified**, with no new issue closure.
Dependency enforcement, IO-023 native-parent leases, legal/SDK ambiguity,
38/42 staged coordinates, ABI/consumer/minimum-platform and full-CI gates remain.

The final [source-held preflight004](evidence/ci-preflight-20261027-004/lead-review.json)
passes all21 commands with **824 Python tooling methods**, including144 CI
methods, strict MkDocs and actionlint. All13,887 Git-listed inputs were unchanged
during the run and before independent archive. These are tooling checks, not
new Android/UIKit/library/consumer executions. The generated local-only docs
site used owned tmpfs to retain the8GiB reserve; its441 files/31,222,830 bytes
were [hashed before owned cleanup](evidence/owned-docs-site-cleanup-20261027-004.json).
This paragraph/archive are additive after the held check, not a circular
immutable-revision or release-readiness certification.
