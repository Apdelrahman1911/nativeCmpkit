# Actual Android failures and contained follow-up — 2026-10-27

Single-agent development continues on `development/preview-hardening`. Actions
remain enabled/all/no mandatory SHA pinning with read-only verification tokens.
Publishing, releases, snapshots, deployments and Pages remain gated. No issues
are closed by these results; the164-finding ledger is unchanged.

## Reviewed immutable Android run

Run [40436756084](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40436756084)
at `ab213b4016eed66bf92ab067bb867d4b1fdfb9bd` is **failed**, not a release pass.
The [independent Git/ZIP/XML review](evidence/github-actions/40436756084/lead-independent-review.json)
reconstructs all704 selected source inputs from immutable Git blobs, verifies the
159,361-byte artifact's SHA256, guards both AGP directories/serial identity,
recounts actual XML elements and checks report timestamps/task markers.

| Library | Actual executions | Pass | Fail | Skip/error |
|---|---:|---:|---:|---:|
| IO | 17 | 17 | 0 | 0 |
| Picker | 25 | 24 | 1 | 0 |
| WebView | 25 | 24 | 1 | 0 |
| Total | 67 | 65 | 2 | 0 |

Tooling job passed; APK assembly exit0/362.12s, connected command exit1/135.07s.
The owned API35/x86_64 emulator is Enforcing, boots and exits cleanly with no
forced termination. These are emulator/library outcomes, not physical-device,
minimum-API, packaged-consumer or complete native-feature certification. Earlier
collector failures remain preserved; missing uploaded XML never proved no bodies
ran in those attempts.

## Picker's real hard-link precondition remains open

`SaveDestinationDeviceTest.actualHardLinkIsNotTruncatedOrDeleted` throws real
`ErrnoException: link failed: EACCES` at immutable line90, **before save assertions**.
There is no demonstrated production identity failure in this outcome. Actual
same-device/same-inode/nlink, original bytes, both surviving aliases and descriptor
cleanup are still required; no fake inode, assumption skip or successful export
is substituted.

The [read-only AOSP reference](evidence/android-hardlink-policy-reference-20261027/source-reference-receipt.json)
is tag `android-15.0.0_r1`, commit `ad1c4255c49d57fe885894a8b690c0dfd542100b`:

- `public/global_macros:31` defines `create_file_perms` without `link`.
- `private/app.te:245–254` uses that macro for app sandbox files.
- `private/shell.te:489–495` explicitly prohibits shell hard-linking:
  `neverallow shell file_type:file link;`.
- Inspected `private/runas_app.te` adds execution/debugger privileges, **no link
  grant**. A proposed `run-as ln` is not a verified remedy.

These limited reference files are **not the installed emulator's complete
policy**, and no AVC/installed-policy cause is claimed. The root LICENSE fetch
returned an HTTPError (status was not captured); that failure is retained. Only lookup metadata/hashes, not raw policy
distribution or generic license substitutions, are archived. No root, permission
weakening or SELinux mutation was executed. A safe real pre-provisioned hard-link
fixture remains to be established before this test can pass. The original failing
case and its assertions remain unchanged and fail closed.

## WebView fixture repair, not yet a native pass

`AndroidWebViewHistoryDeviceTest` reaches initial readiness and its original
script callback, then times out at immutable line51 waiting for native backward/
forward/#first history. **Navigator replacement assertions were never reached.**
The old failure recorded no native URL/index/flags at timeout. Chromium's
history-manipulation intervention for entries created without user activation is
a hypothesis, not a demonstrated production cause.

The current fixture mounts the public WebView full-screen and sends real Compose
touch input to a local HTML button. Only its actual DOM click creates the two
history entries. It explicitly verifies active browser user activation, one click
and the second fragment before going back. Original native backward/forward,
replacement/same-instance and lifecycle-count assertions remain. A bounded
timeout diagnostic records actual native history/URL/index; the predicate is not
relaxed. This source repair still needs a fresh immutable emulator run.

The finite `android-webview` profile runs only the failed WebView module, avoiding
repeat of passing IO and the unchanged known picker failure. The default
`android-device` profile still requests all three. The controller now passes an
explicit subset identically through discovery, APK assembly, connected execution
and receipts. It reports incomplete coverage rather than silently omitting tests.
The [tooling regression pair](evidence/android-webview-subset-contract-20261027/lead-review.json)
retains red150 (144pass/3fail/3error) and green150/150. Green inputs are held before/
after execution and archive; red inputs were captured only after red/before
repair, a stated limitation. **Zero Android/library methods** run in Python mocks.

## Actual KGP worker result parser now exercised on Linux

The [preserved diagnostic](evidence/kgp-native-worker-parser-20261027/lead-independent-review.json)
uses actual Kotlin/Native2.4.20, Gradle9.7.1/JDK17 and KGP `KotlinNativeHostTest`:
positive2pass/Gradle exit0, intentional-negative1pass/1fail/Gradle exit1, two fresh
JUnit XML reports. Worker2 bodies and termination before process exit are observed.
This is **four repeated diagnostic executions/two methods/zero library or iOS
tests**. Failed setup attempts and the first review's incorrect exit expectation
are retained. Successful unchanged binary compilation was reused, not test XML.

KGP deliberately supplies `--ktest_no_exit_code`: the native runner returns0 in
**both** runs, while real TeamCity/JUnit failures correctly fail Gradle. Do not
require native exit1 under that protocol, nor infer test success from an app's
completion marker alone. Genuine UIKit linking/application launch/presentation,
native-parent leases, ordinary root/convention dependency enforcement, legal/
provenance, strict packaged consumers, ABI and minimum-platform gates remain open.


## Source-held preflight before immutable CI

[Preflight006](evidence/ci-preflight-20261027-006/lead-review.json) passes21 bounded
commands/830 Python-tooling methods, including the same150 CI methods. Strict
MkDocs, installed-docs compatibility and actionlint pass. All captured inputs
remain unchanged through execution and before archiving. Zero library/native/
consumer methods run. This additive receipt/link follows that freeze and is not
circular certification of a later commit; the WebView emulator rerun remains
pending. No publication or issue closure occurred.
