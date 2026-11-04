# Preserved camera HOME baseline — 556–559

**Local source/JVM/compiler qualification only. #13 remains open.**

The original [41729467621](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41729467621)
still fails before Gradle/native execution. Its bounded observations identify a
retained empty HOME/FallbackHome-shaped record, not an owned standard Settings
task. This patch does not reconstruct that actual record or certify the installed
image's source revision. It fixes the previously empty-only admission contract
without purging or silently ignoring preexisting data.

## One owning patch

The Kotlin common-test and Python parsers require one **complete thirteen-row**
bounded ASCII FallbackHome record: fixed user0/UID1000/bootstrap caller0/null
caller and feature/setupfalse, exact HOME intent/component/affinity, empty
Activities, finite known policies, matching bounded leaf identity and separately
preserved root identity, no child PiP, and bounded original activity clock.
Missing/extra/duplicate/out-of-order/live/foreign/standard records fail. The
source-template unprinted default root-policy row also fails. Only recent-list
rank and elapsed inactivity seconds may change; every other relevant byte is
preserved, including task-object identity and original `lastActiveTime`.

This is **nonowned, never removable** data. Formatting is redacted. Python admits
only complete empty framing or one fully parsed HOME record; command completion,
exit/stderr and output bounds remain independently mandatory.

- `OwnedDeveloperPrerequisite.snapshot` carries the exact baseline in the two
  complete stable snapshots. Same-epoch appearance, disappearance, replacement or
  drift fails. Only the existing latched normal-reboot cleanup may observe a new
  epoch; two equal snapshots are required before storing its epoch and baseline
  together. Later new-baseline drift or an old/foreign epoch fails.
- The existing master writes, reporter uninstall and sole reboot now revalidate
  HOME preservation at their **own IPC boundary**, with kernel identity checked
  before and after the returned recent-task query. This repairs a confirmed gap:
  earlier snapshot checks alone did not protect those later actions.
- `OwnedDeveloperSettingsUi` verifies the installed platform Settings/FallbackHome
  component, captures the nonowned baseline only before launch without an active
  lease or competing owned task, and rechecks it on every later recent-task read.
  Both owned leaf/root IDs exclude **both** preserved HOME identities. A missing
  owned-leaf-versus-HOME-root comparison was confirmed and repaired.
- The original nonce/caller/component/top-resumed ownership, genuine preference
  actions, exactly-once removal, accessibility-resource recycling, flag restoration,
  strict live-task reader, native/scalar restoration and primary-error cleanup
  remain. There is no force-stop, task sweep, guessed root equality, root/DPC
  elevation, native assertion bypass or live-HOME ignore waiver.

Six changed paths /18 exact reversible fragments, plus seven new parser/test/
history inputs, form the owning patch. Historical fixture entry points peel only
its full declared afterimages before retaining their old pins. Latest-source
admission is explicit at the shared top entry. Old/unknown/partial/displaced
images cannot substitute for the latest source. Historical fixture acceptance
does **not** certify new HOME behavior. Production, public APIs, original native
method bodies, workflows and dependencies are unchanged.

## Important results, failures retained

| Population | Actual result |
|---|---|
| NEW parser/controller15 | First10 pass/one failure/four errors; only failed5 recover5/5 |
| NEW epoch/action7 | First3 passing/four failed methods/five failure records; only failed4 recover4/4 |
| Affected epoch acceptance1 | Pass1/1 after action-guard changes; not an unchanged replay |
| History controls | First7:6 pass/one current-entry refusal; later changed/new3:1 pass/two image-domain assertions fail; only failed2 recover2/2 |
| Related affected fixtures14 | Pass14/14 once, unittest3.531 s /wrapper3.904447 s |
| Genuine library JVM regression8 | Pass8/8, one fresh XML/no skips, Gradle0/48.03 s |
| Fresh Android instrumentation compiler/APK | Gradle0/40.01 s, one fresh local APK; **zero device executions** |

The boundary runner initially subtracted failure records instead of distinct
failed methods and reported2 passes; its preserved readback corrects this to3.
The history review initially equated an immediate beforeimage with an older
composed ancestor; the exact older pins/chain are now checked separately. The
first warning classifier incorrectly treated every `w:` record as a file
diagnostic; all **nine** records remain: five Kotlin file warnings and four
host/native-configuration warnings. These are reviewer/fixture failures, not
native failures or permission to conceal warnings. A `python`-executable lookup
failed before any tests; the actual commands use `python3`.

The [solo source/results review559](source-results-review559.json) accepts53
passive checks, six full own-Git beforeimages and18 unique forward/inverse
fragments. **All1,320 current local inputs match the successful APK compiler
snapshot exactly.** Earlier common8 results are reused only on the two unchanged
common parser/test sources; their1,317-map receipt is not relabeled current.
The actual XML digest is in `common8.json`; an earlier handoff-summary typo is
not evidence. All accepted unchanged test populations are reused, not rerun.

Seven resize-mode literals match separately acquired public
[`ActivityInfo.java`, Android15 tag](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-15.0.0_r1/core/java/android/content/pm/ActivityInfo.java).
The cached Task.dump policy/ordering/print conditions were also reviewed. This
is source-template evidence, **not installed emulator-image provenance**.

## Next and limits

Freeze this qualified development patch, read back current combined hosted
capacity, then request **only the missing Dont-keep C1**. Retain the actual
readable exactly-once capture, native/scalar/master restoration and owned cleanup
criteria. Do not replay accepted camera009 C2/C3, common8, unchanged APK builds
or the previous failed native request. Any new refusal needs original evidence
review before another owning repair; baseline parsing alone grants no task
ownership or native acceptance.

This batch is uncommitted at `afcc8076dd175e36a221b09b446f4213bc4c6bd1`; no Git,
dispatch, issue/comment/closure, main, release/package/deployment or Pages mutation
occurs.103 closed/69 open/172 total remains. No hardware/provider/native memory,
consumer/API–ABI/dependency/legal/security or release readiness is inferred.
SOLO, serial local builds/8 GiB reserve, max2 combined hosted reservations
INCLUDING queued, read-only Actions/all/no mandatory SHA pinning and every
independent publishing/security/readiness gate remain.

See [maintainer testing instructions](../../../../testing/camera-home-baseline.md).
