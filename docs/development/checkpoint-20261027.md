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
