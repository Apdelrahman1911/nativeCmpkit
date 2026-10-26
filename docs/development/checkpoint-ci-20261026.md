# Hosted CI failures and contained follow-up — 2026-10-26

Control remains [single-agent, authorized verification, contained
publishing](containment.md). `main` stays at the upstream synchronization
checkpoint. Neither a successful host suite nor a source/test patch clears a
release gate. Historical failed attempts and all 164 original acceptance records
remain unchanged.

## Reviewed immutable executions

The [hosted ledger](evidence/github-actions/README.md) binds every result to
`6eb7c66eb01b390353100c63882cd102846c7b8d` and its actual host/runtime. Core passes
831 fresh executions; macOS passes426 including real AppKit cancellation. Apple
and Windows workflows still **fail**. iPhone executes348 (332pass/16fail), with
zero WebView tests after its production compile error. Windows executes422
(421pass/1fail), plus one N/A and four unexpected filesystem-policy skips.
No successful same-input desktop job is blindly rerun as a response to iOS errors.

## Follow-up preflight and upstream reconciliation

The [held-source preflight](evidence/ci-preflight-20261026-002/lead-review.json)
passed all21 commands:801 Python tooling methods, including121 CI methods,
strict MkDocs and actionlint1.7.12 on the **two actual workflows**. All13,436
nonignored Git-listed inputs remained unchanged during the check and before
archive. This is a dirty snapshot based on6eb7c66, not a release candidate;
the archive and this additive documentation are subsequent inputs. These801
methods include mocked emulator/controller cases, **zero new library/native or
packaged-consumer executions**. No prior failure or acceptance requirement was
deleted or relaxed.

The [subsequent staged hygiene review](evidence/staged-hygiene-20261026-001.json)
found26 trailing-whitespace warnings, **all in newly archived raw build/CI logs**.
Their exact hashed bytes are deliberately retained. The full staged check exited2;
the separately scoped non-log source check exited0. All700 selected library/build/
CI inputs still match the passing preflight. Do not trim evidence logs or call
the full staged check successful.

The [fresh read-only remote observation](evidence/remote-preflight-20261026-002/observation.json)
again found16 open Calf issues, with original descriptions, authors, timestamps,
labels and comment counts unchanged from the completed synchronization; one open
PR is excluded. No duplicate import or new mutation was needed. Actions remain
enabled/all/no-required-pinning, default tokens read-only, Pages status null and
legacy branch publishing off, `main` unchanged, zero GitHub releases, and no
unfinished run in the returned100-run page. This timed observation is not a
package-registry or fresh public-HTTP Pages audit.

## Owning-source repairs and fixture diagnosis

| Observation | Current work | Evidence boundary |
|---|---|---|
| Android ordinary openable provider receives DocumentsProvider-only MIME columns; independent size/MIME regressions fail | `KmpFile.android.kt` uses `ContentResolver.getType` for ordinary content URIs while preserving `DocumentFile` document/tree handling | Local red24:21pass/3fail; green24/24, same three new regressions. [Red](evidence/openable-metadata-red-001/archive.json) / [green](evidence/openable-metadata-green-001/archive.json). Robolectric, not proof the original device004 provider failure is fixed |
| iOS arbitrary/RectangleShape forwarded into Backdrop2.0.1 lens crashes at `LiquidGlassButton.kt:118` | Keep the requested outline/blur/surface; apply the rounded-rectangle lens only to its supported shape families | Original runtime failure preserved. Repaired iOS execution pending; no public signature removed |
| iOS single-date selection scrolls April's displayed month back to March | `CalendarViewHost.preservingVisibleMonth` suppresses transient owner-navigation reports and restores the native visible month around nonanimated programmatic selection | The original native assertion fails at test line55, **after** selection update, not initial month creation. Added selection/null/callback assertions; native rerun pending |
| iOS WebView's nullable native cookie list fails compilation | Use the nullable list's empty collection adapter before cookie type filtering | Apple production compile failure retained; runtime cookie/lifecycle tests still required |
| iOS icon/switch tests assert colors immediately after a `runOnIdle` state write | Await resulting recomposition before the unchanged color assertions | Compose1.12's exact source shows `runOnIdle` waits **before**, not after its action. This is a fixture-ordering repair, not established production color loss |
| Picked Unicode URL returns canonical decomposed accents | Compare exact source/copy native filename components plus canonical equivalence to the requested name | Do not rewrite production filenames. All source-preservation, deletion and idempotent release assertions remain; Apple rerun pending |
| UIView hit-test result has the same native pointer but a different Kotlin wrapper | Test NSObject/UIView native equality, not Kotlin wrapper referential equality | Native identity remains required; no hit-test assertion is dropped |
| Seven UIKit presenter/interop tests fail before their operation on missing `LocalUIViewController`; target/action and MIME lookup fail under the standalone runner | Investigate the exact Compose Skiko test source and Kotlin/Native executable launch contract; provide a genuine UIKit application/window host rather than fabricated locals/stubs | These failures are preserved, not dismissed as successful native behavior. UIApplication/application-host execution and native outcome verification remain pending |
| Windows path test hardcodes Unix `/tmp` as absolute | Construct an absolute path using the actual host's temp directory and retain exact roundtrip assertion | `java.io.File` root/drive semantics explain the fixture failure; revised Windows execution pending |
| Four Windows tests skip POSIX/symlink assertions | Review Windows ACL/reparse handling and require equivalent actual filesystem tests | No new blanket skip/N/A exception or false Windows pass |

## Actual Android CI setup work

The explicit `android-device` profile uses one API35/google_apis/x86_64 KVM AVD,
with SELinux **Enforcing**. Only the ephemeral runner's KVM ACL is adjusted. The
controller requires a clean Linux x64 source, unused ports and empty device table,
owns its unique AVD/home/process group, rechecks identity/security, and separately
records setup, test and teardown outcomes. Nonzero native teardown is an overall
failure even if tests passed. IO runs before picker/WebView. No personal device,
SELinux override, sample substitute or package upload is permitted.

Adversarial mocked controller/CI tests do not execute an emulator. Actual local
APK assembly and AGP connected-task configuration passed under700 unchanged
selected inputs: assembly exit0/47.02s (163tasks,17executed/146up-to-date), dry-run
exit0/25.01s (9up-to-date build-logic tasks). [Receipt](evidence/apk-contract-001/receipt.json).
**Zero library/device tests**, and no connected-task `doFirst`, executed there.
Subsequent plan ordering/checkout-byte changes need their new immutable CI run.

## Actual Maven staging attempt remains failed

The [local-only staging](evidence/maven-staging-001/archive.json) used candidate
`0.1.0-preview.1`,696 held dirty inputs and no publication credentials. Exit1
after178.23s;793 tasks (657executed/41cached/95up-to-date), **zero tests**. Only
38 of42 requested metadata+desktop coordinates staged (19 of21 roots). Picker
and share correctly failed `verifyPublicationNotices` on incomplete locked
native license materials. Preserve the partial repository and file hashes; do not
weaken the guard, silently overwrite it, or count producer staging as a consumer.

The prior16 archive-text gaps per module, separately pinned JNI texts for one,
remaining15 objc2-family full-text gaps and Apple SDK-derived-work ambiguity are
not legal clearance. **Zero of17 strict Maven Kotlin consumer methods executed.**
All other targets/minimum-platform/ABI/dependency/security/distribution gates
remain as listed in [release readiness](release-readiness.md).

## Local storage boundary

Other projects share this host. A small native binding probe was refused at the
8GiB reserve before it started. Only six **this-project generated MkDocs sites**
were removed, after preserving their exact file hashes in the
[cleanup receipt](evidence/owned-output-cleanup-20261026.json). No source, repository,
test report, log, dependency cache or other project was removed. Subsequent
builds retain the reserve; use hosted verification where capacity is unavailable.
