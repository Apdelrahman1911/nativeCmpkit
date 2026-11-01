# Android Local2 original review — run 41357684810, attempt 1

**FAILED: 2 native executions, 2 failures, 0 passes, one fresh XML.**

- Repository: `Apdelrahman1911/nativeCmpkit`; branch: `development/preview-hardening`.
- Immutable SHA: `6c8684a3b9ad078efea2eb991d7c6243704bbd2d`.
- Profile: `android-io-named-system-providers`; only the two methods of `AndroidIoNamedSystemProviderTest` identified in `verification.json`.
- [Original run](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41357684810) ended failed on 2026-11-01. Actual library job: 22:35:45–22:44:59 UTC.
- Native Gradle **exit 1 / 114.06s**. Separate reporter APK assembly **exit 0 / 313.09s**; neither assembly nor tooling is a native pass.

## Different original owning failure boundaries

| Local provider | Native UI call in `NamedSystemDocumentsUi.kt` | `samplesCapped512` | `maxVisibleMatches` |
| --- | --- | ---: | ---: |
| ExternalStorage | Open-tree-button click, line 46 | 265 | 0 |
| Downloads | Owned-folder-row click, line 35 | 192 | 0 |

Both failures originate at `find`, line 245, through `namedProviderCase`, line 71. The strict 20-second UI gate is unchanged.

`maxVisibleMatches=0` is the maximum **fully eligible selected candidate count** across processed qualified-root queries. It is not a raw-node count, a known last-poll operand, proof that a button/folder is absent, or a failure cause. Individual query/filter operands and causes remain **unlogged/unknown**. No relaxed selector, guessed namespace or blind retry is qualified.

## Source-conditioned reached checkpoints, not completed methods

The actual failure locations, bound to unchanged immutable native source, occur after stock API35/English/user0/background and ownership prerequisites, exact system-provider identity, owned published MediaStore seed and genuine implicit system DocumentsUI dispatch. Both get past the **complete six-role literal resource admission** before their accessibility query. The admitted system-app/namespace variant is not logged.

ExternalStorage also gets past its exact owned-row `ACTION_CLICK` returning true, the exact toolbar-folder observation and admitted open-tree label resolution. Downloads stops at its first owned-row click gate. These are source-conditioned reached checkpoints only, **not new completed native passes or fulfillment of Local2 criteria**.

Both stop before the test reads/verifies its ActivityResult URI and grants. Public `KmpFile` metadata, bounded read/descriptor ownership, bookmark persistence/restore/release and post-release refusal assertions are **not reached**.

## Runtime, XML freshness and source custody

- Recorded actual runtime before/during/after: **API35 / Android15 / x86_64 / SELinux Enforcing**, official Google APIs image revision 9, emulator 37.2.13; Linux x64, JDK 17.0.21 and Gradle 9.7.1. Explicit owned AVD/serial and the one actual connected-task protocol hold.
- Exactly both required identities fail once in one XML; no extra, missing, duplicate or skipped native case. Its timestamp is inside the actual library/job window and binds the newly owned device.
- XML producer filename suffix `15` denotes the Android release, **not API15**. Outer XML `time=0.000` is preserved; actual case times 29.549s / 22.483s and suite 52.032s are not zero-native evidence.
- **All four actual 1179 library before/after maps exactly match frozen Git inputs**; native source-contract, runtime and input-digest bindings hold. **1257 canonical combined inputs are frozen Git provenance only**, not actual hosted combined maps. The workflow is canonical-only, outside the 1179 library maps.
- Mandatory hosted tooling's main 2287 methods pass, but remain tooling, not library/native acceptance. This reviewer replays no controls or accepted populations.

## Cleanup and diagnostic limits

The separately recorded owned-engine shutdown is **graceful request / actual child exit0 / no forced fallback / clean shutdown true**. Neither failure XML surfaces a suppressed cleanup exception. The unchanged native `finally` retains exact conditional owned-row cleanup and UIAutomation flag restoration, but there is **no separate native-finally cleanup receipt**; do not elevate it to an independently verified cleanup pass.

This Local2 controller records **no separate adb-transport absence or AVD-filesystem/empty-directory disposal receipt**. Those outcomes are not claimed. Full Gradle/APK/logcat bodies were not uploaded: the originals retain bounded Gradle excerpts and hashed file inventories, not the missing bodies or historical poll operands. Retained emulator warnings are not assigned causal significance.

## Once-only originals and independent review

The sole reviewer acquired one original logs ZIP and one artifact ZIP once each after terminal; no reacquisition. All 32 log and 21 artifact entries were safely inspected/extracted as regular files, never executed. GitHub artifact run identity/size/digest match its downloaded ZIP.

- Logs ZIP SHA256: `d66da0a59bd31c7854cd90a4bfd389bd7c92a2150296a5bfc6c562bc1feba962`.
- Artifact 13104312317 ZIP SHA256: `2db010b4e1038b15a5533e3ba64a57eff6779511c0d30d5caa2f2f968d035b75`.
- Fresh XML SHA256: `f931418355006bd3c882b13f7c2447eb0f42e55d4096fe52b1c6a5f229b426eb`.

**55 passive original/source/result/runtime/custody checks are satisfied**; they are review checks, not native tests. 24 immutable source snapshots are reviewed. Two reviewer-only digest/map-membership refusals are retained and resolved from exact source serialization and library-versus-canonical scope; no original bytes or native result were repaired. Repository models/tests/builds/native/browser executions, Git mutations, dispatches, comments, closures and publishing by this reviewer: **zero**.

**#55/IO-019 stays open. Local2 remains missing; cloud C1 is separate and missing.** No physical/vendor/minimum/whole-platform/packaged-consumer/API-ABI/dependency-trust/legal/security/publishing/Pages/main/history/release-readiness gate is lifted.
