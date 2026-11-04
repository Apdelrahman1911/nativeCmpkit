# Share650 successor: the existing profile now selects only AppKit6

**Source/model preparation, not a native result, readiness fix, issue closure,
trusted-builder attestation, consumer result or release permission.**

## Why this is missing-only

Original `41791895471`, attempt 1, source
`ef6aae6da0c0879431d9c4712f8f914eaf6194ea`, remains **FAILED**. AppKit compilation
finished successfully; `missing_content_view` failed in the owned-window
key-wait at `calf-share/native/tests/appkit_lifecycle/cases.rs:61`, called from
176–178, before its nil-content/native admission body. Five later cases were
unexecuted. The predicate is `window.isKeyWindow()`; the actual readiness cause
is **unknown**, not an inferred activation/run-loop/library bug. The original
cached evidence is acquired/reviewed once; this follow-up does not reparse its
private panic stream or convert compilation/cleanup into native acceptance.

All three authored JNI methods are cumulatively accepted, including the original
650 timeout method. They must **not run again**. Original 630 accepted AppKit
`cancel_before_dispatch` and `no_key_window`; these must not be selected either.

The separately reviewed observation609 prerequisite records one finite,
sequential, read-only late snapshot only after the original key-wait panic and
before independent owned cleanup. It preserves original actions, predicates,
10-second deadline, native assertions, cleanup and primary failure. It is not a
readiness fix; if the key wait fails again, it stays failed and later five stay
unexecuted. Original609 NEW14 red → only failed14 + affected6 =20/20 chronology is
retained and not replayed. Prerequisite seal
`7a1d599ee6b1d79e215fb2dea1d1802bcd49ac2373e870be908517c5248133b3`, manifest
`dd5872cb1a7e23beb064dfcad7ef10544e0b547d734498b564dd73ae5ee3a0e6`.

## Existing workflow, no extra profile/job/test run

Keep `macos-share-missing-lifecycle`, its workflow option, matrix and permissions
byte-identical. Its preceding AppKit step already compiles once and requests
these six serial, fresh processes, stopping on the first failure:

1. `missing_content_view`
2. `real_picker_cancel`
3. `controlled_picker_dismissal`
4. `controlled_success_duplicate_late`
5. `controlled_service_failure`
6. `bounded_concurrent_requests`

The owning missing-only controller now records the actual GitHub repository,
workflow, job, run/attempt, source SHA/ref, slot and finite selector **before
compilation**. Missing/foreign context refuses; other controller modes remain.
The following existing `library_tests.py` CLI entry redirects only the exact
`macos-share-timeout-retention-recovery` focus to a passive same-job reference.
It executes **zero Gradle, JVM/JNI or AppKit commands**, and writes only its own
fresh `build/ci-verification/desktop-macos-arm64/receipt.json`. Its plan exposes
six original Rust cases and actual AppKit report-copy paths, not a JVM task or
synthesized fresh JVM XML. Direct internal `library_tests.run` with the retired
focus refuses before output/command work. The old `library_tests.plan`/JNI model
oracle remains historical source context, not a permitted live execution path.

The existing workflow comment “JNI timeout below remains independent” is now
outdated. Do not rewrite that comment/workflow during a trusted-CI freeze merely
to refresh wording; this document records the correction. Default eight-case /
other library profiles remain unchanged. No workflow/matrix derivative is
qualified by this local successor packet.

## Same-job reference gates

`macos_share_appkit_only_route.py` requires exact run **and attempt**, job,
profile, slot, source SHA/ref and a recent bounded parent from this job. No
cross-run cache or accepted JNI receipt may replace it. It checks:

- Full source/native before/after maps captured by the exact owning controller,
  their declared counts/digests, every current listed source byte and required
  native build/reader inputs. The independently reviewed actual producing job is
  still required: receipt consistency is not cryptographic builder provenance.
- Clean same-source Git, held actual macOS-arm64/Rust/Cargo/Xcode/SDK/tool file
  identities and opted-in graphical-session observation; no visible-picker or
  recipient delivery is inferred from the session probe.
- One admitted fresh executable's Mach-O CPU/type, mode, source binding and held
  ordinary file identity; successful bounded compilation with independent owned
  process-group cleanup and the two original private-log identities.
- Six ordered fresh/distinct owned process receipts, strict successful exit and
  unforced/reaped/empty-group cleanup; exact current source/runtime/artifact maps.
- One exact original Rust XML and one actual finite private stdout marker per
  case, actual PID paths, fresh original bytes and exact copies; no skipped,
  substituted, duplicated, missing or additional reports.
- The complete preserved original-report inventory, all observed source/data
  identities again at the end, and actual absence of the released owning lock.

Private raw logs are not published by this reader. It observes only the finite
stdout marker needed for case/owner-cleanup agreement. The failure-only609 reader
is separately responsible for its bounded late fields. Descriptor-rooted reads
and sidecar writes reject symlinks, aliases, traversal, changed parents/files,
foreign outputs and unverified ancestor creation; cleanup is independent and
preserves primary failures. Reference failure cannot make the job green.

## Source controls and remaining work

`python3 -B -m unittest -v scripts.ci.test_macos_share_appkit_only_route607`
contains only genuinely NEW source/inverse/CLI/model/file-custody controls.
Synthetic Mach-O headers, fake GitHub context, model PIDs/runtimes and model XML
are ordinary temporary fixture data, never executable/native/host evidence.
No accepted native/JNI, observation609 or older control population is replayed.
Exact current admission and exact history peeling are different domains; retain
all old manifests/pins. Lead must compose the newest layer before shared/dated
comparisons without accepting old bytes as current or rewriting historical pins.

Next: integrate observation609 separately, integrate this three-path successor,
independently qualify outer CI/history/current-source composition, freeze/push,
check fresh capacity and dispatch **only missing AppKit6**. Independently review
actual source/runtime/PID/XML/log/cleanup originals before any issue action.
`#84`, `#85`, `#150` remain open; visible picker/service/recipient, Instruments,
leaks/ASan/stress, remaining platforms and original criteria remain separate.
No release/package/deployment/Pages, API–ABI, dependency, consumer, legal,
security, attribution, Git-history, main or release-readiness gate is waived.
