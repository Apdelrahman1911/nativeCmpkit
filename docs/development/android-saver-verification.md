# Android saver: verified original data-loss fix

**IO-002 / #5 closed on2026-10-27 after required tests and source/results review.**
[Acceptance](evidence/android-saver-acceptance-closure-20261027/acceptance.json) and
[closure readback](evidence/android-saver-acceptance-closure-20261027/closure.json)
retain original criteria/body/title/labels and every prior expanded remaining item.
17 total closures at this observation; no packages/releases/deployments.

## Required tests and accepted execution

- [Host40414284598](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40414284598),
  immutable6eb7c66: **35/35 picker host methods**, eight XML, host job exit0.
- [Android40436756084](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40436756084),
  immutableab213b40: **8/8 actual FileSaverActivityDeviceTest methods**, real
  ActivityResult/recreation/provider descriptors, API35/x86_64, SELinux Enforcing.

| Original criterion | Passing methods |
|---|---|
| Compose launch/recompose/result for bytes and KmpFile | `bytesAreWrittenWhenTheResultArrivesInALaterComposition`, `aFileIsCopiedWhenTheResultArrivesInALaterComposition` |
| Activity recreation, URI and ByteArray | `uriPayloadSurvivesActualHostActivityRecreationBeforeTheResult`, `lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess` |
| Cancel clears payload | `frameworkCancellationDeliversOneNullResultAndReleasesTheNextLaunch`, `aCompletedRequestDoesNotRestoreAsAnotherOutstandingSave` |
| Repeated/concurrent policy | `consumeIsExactlyOnceAndRejectsOverlapUntilWriteFinishes`, `overlapReportsOneErrorWithoutReplacingTheAcceptedNativeRequest` |
| No unavailable-content no-op success | `savingAMissingFileToItselfDoesNotClaimSuccess`, lost-byte error above, `failedDistinctProviderSourceDeletesOnlyTheNewDocumentWithoutWritingIt` |

These are explicitly **reused already-executed results, zero new executions**.
Current Android/device/source/dependency inputs matchab213b40 except exact root/POM
display strings. Host owning sources also match, except `KmpFile.isDirectory`'s
unrelated metadata query, which the saver does not call; the later actual device
revision already contains that repair. Named source methods/XML hashes were inspected.
The review's initial path-spelling assertion failure stopped before any mutation;
the exact owning path correction preserves all five requirements.

## Owning repair and compatibility

`FileSaverLauncher.android.kt` uses one `rememberSaveable` `PendingSaveSource` for
both remembered launch lambdas and updated result callbacks. `set` rejects an
accepted overlap, `consume` transfers/clears once and `finish` releases pending
state on cancel/write completion. URI payloads restore. Large ByteArrays are not
put in the Activity Bundle: restored missing bytes deliberately fail and clean
only the new destination, rather than pretending an empty export succeeded.
Actual recreation and source/descriptor assertions confirm that policy. Public
signatures/packages remain; null bytes still intentionally mean an empty file.

## Independent gates still open

**The complete device workflow remains failed:** picker24/25 plus unrelated
WebView history failure. `SaveDestinationDeviceTest.actualHardLinkIsNotTruncatedOrDeleted`
fails at actual `Os.link` EACCES, before save assertions. This is retained under
**open BUILD-006/native release coverage**, not waived, skipped or relabeled.
The source/data-loss issue's five original criteria are complete; closing it does
not certify that separate Android kernel scenario.

Expanded prior destination-zero/unknown-identity/provider, full OS process death,
persisted grants/restarts, physical/minimum API, lifecycle/concurrency and consumer/
API-ABI/security checks remain in the acceptance record and
[release-readiness](release-readiness.md). No security policy is weakened to obtain
a hard-link fixture and no Unix-host hard link is called an Android pass.
