# Contained UIKit execution and partial packaged-consumer follow-up

This is single-agent development under the owner's reaffirmed **2026-10-27
containment**. Verification Actions remain enabled/all allowed, without mandatory
SHA pinning, with read-only token permissions and no persisted checkout
credentials. No package, release, snapshot, deployment or Pages is authorized by
the observations below. `main` remains at the issue-sync checkpoint; development
history and the original 164 findings are preserved.

## Real UIKit execution — failed, not a successful application suite

[Run40468870504](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40468870504)
at immutable `b5a4508a8d28f9937c456db2895b4ae09c4a9343` passes tooling, but its
macOS26/Arm64 iPhone-simulator job fails. The [independent Git/ZIP/XML review](evidence/github-actions/40468870504/lead-independent-review.json)
reconstructs all **712 selected inputs** from Git and matches the before/after
receipts. Actual Gradle exits **1/1755.81s**, with **82 executions:81 passed,
1 failed,0 skipped**, in15 XML reports. Those81 outcomes are not81 new genuine
application scenarios.

The genuine application activates **main Worker1/owned Worker2**. Its first
mandatory native method, `presentedAlertUsesLatestActionAndTextFieldCallbacks`,
fails when Compose asynchronously aborts at `PlistSanityCheck`: the generated
application's `Info.plist` lacks Boolean
`CADisableMinimumFrameDurationOnPhone=true`. Only **one of11 mandatory
application methods** appears, and it fails; ten are absent. Transport remains
incomplete. Actual Mach-O link/sign/install/installed-byte readback and exact
owned stop/uninstall/absence/local-bundle cleanup succeed, not native acceptance.

The94111-byte evidence ZIP (artifact12719418131) is retained with digest
`sha256:1c94341683836cc3ff9d27870e57ee22e5a727a57b082a9b59db67593a0b2839`.
Two reviewer-precondition errors are preserved separately: KGP prepends exactly
`iosSimulatorArm64ApplicationTest.` to XML class names; an activated receipt
omits `startup_failure_observation`, rather than containing a null value. The
corrected review does not rewrite original reports or testcase outcomes.

### Owning manifest repair and limits

`scripts/ci/ios_ui_application.py` now serializes the actual plist Boolean.
Two new guards check the serialized value/type and reject disabling Compose's
strict sanity check in the genuine host. [Original32-method red and corrected
32/32 Python pass](evidence/uikit-plist-20261027/green.json) are preserved.
**Zero Apple executions verify this correction yet.** All native identity,
attachment, eleven mandatory methods, transport/XML agreement and owned cleanup
requirements remain. Execute a new immutable **`ios-ui`** profile, not an unchanged
rerun of the crashing manifest. Production APIs are unchanged.

## Gradle module-metadata validator correction

Real Gradle9.7.1/KGP child metadata may identify its owning KMP root with a
canonical relative back-pointer, rather than the target filename's coordinate.
`tests/consumer/verify_artifacts.py` now admits only exact same-version owning
coordinates, root component attributes and reciprocal target variant names,
attributes and redirects. Direct target metadata remains supported; foreign,
recursive, missing, malformed or noncanonical owners fail.

[Red/green metadata tooling](evidence/consumer-metadata-identity-20261027/green/receipt.json),
official builder/writer/specification bytes with their notices, original failed
inspections and [1425-file staging recheck](evidence/consumer-metadata-identity-20261027/staged-bytes-recheck.json)
remain archived. Corrected static inspection passes **308/308 checks for
unchanged older Core/IO staging**. This is not a fresh producer run, executed
consumer, complete published graph, ABI, legal or release gate. Do not restore
the incorrect assumption that every child component must use its filename's
Maven coordinate.

## Explicitly partial independent Core/IO consumer

The unchanged full consumer still requires all **21 publication roots**. The
new [standalone JVM fixture](../../tests/consumer/io-desktop/README.md) deliberately
selects only Core/IO metadata+desktop. It uses no producer project/composite/source,
old-Calf, Maven-local or remote candidate-group fallback. All four selected
compile/runtime/test classpaths must resolve both actual desktop variants and
match staged filenames/bytes/SHA256.

- Six existing IO methods are copied **byte-identically** from the full consumer:
  empty/boundary/large reads, independent concurrent positions, missing/directory
  semantics, Unicode names and repeated-close ownership. They are reused
  scenarios, not six additional independent functions.
- A seventh method verifies actual loaded Core/IO class code-source locations,
  exact desktop JAR names and hashes. Producer class directories or old artifacts
  cannot satisfy it. All seven methods must execute, with zero skips and two
  fresh actual XML reports. A fresh Gradle9.7.1/JDK17 test-task marker is required.
- `scripts/ci/stage-core-io.init.gradle.kts` selects exactly four real publication
  tasks and only the existing isolated **file** repository. The full staging,
  remote/Maven-local/Central interlocks are unchanged.
- `scripts/ci/core_io_consumer.py` copies source-held fixture bytes independently,
  inventories fresh four-coordinate staging, invokes the existing static gate
  with an explicit two-root filter, checks exact resolved bytes and named XML,
  and binds source/staging/fixture/runtime before/after. Failure observations and
  original XML are retained. Private child HOME/Gradle configuration excludes
  inherited credentials and JVM/init/property overrides.
- Finite **`consumer-core-io`** dispatch uses a separate Linux job after tooling,
  an empty library matrix and no repeated platform suites. It uses only existing
  actions, exact runtime/dependency-input cache keys, no prefix restores/build
  outputs/XML caches, and uploads JSON/XML only, never packages. Execution is
  bounded4200s/90-minute job with an8GiB reserve.

The initial controller incorrectly treated read-atime changes as mutations:
32-method red has two errors. Stable content/owner stat fields repair that
contract; both red source files are recovered byte-identically against their
original SHA256 receipts. [Final scoped held tooling review](evidence/core-io-consumer-controller-20261027/lead-review.json)
passes **35 controller/23 workflow/143 full consumer-tooling methods** and
actionlint: **201 Python methods across40 held inputs**. Counts overlap earlier
32/133 runs. Positive fixtures use inert synthetic artifacts/XML and mocked
invocations, not Java/Gradle/library execution.

**The actual Kotlin DSL adapter, staging and seven-method Kotlin consumer have
not executed yet.** Ordinary dependency trust is not certified; the bounded
controller attests its process group, **not detached Gradle daemon/other
descendant cleanup**. BUILD-007 remains unresolved. Hosted immutable verification
is required; root free capacity is below the8GiB heavy-build reserve. No unrelated
caches/projects/installations were moved or deleted, and original capacity/
preparation/guarded-relocation failures remain [archived](evidence/core-io-local-capacity-20261027/root-reserve-rejection-before-Gradle.json).

## Ledger and next verification

The owner ledger remains **87 implemented/69 partially-verified/8 unresolved/
0 verified**. None of these tooling/source observations closes an issue. The
[earlier BUILD-007 progress comment/readback](evidence/issue-progress-20261027-b5a4508a/attempt-2/receipt.json)
and [immutable UIKit dispatch/422 rejection](evidence/immutable-ios-ui-dispatch-20261027-b5a4508a/dispatch/sha-dispatch-rejection-observation.json)
are preserved, not new mutations from this follow-up.

Stage the final intended sources and run both cached/worktree whitespace checks,
the full source-held offline preflight, strict MkDocs and actionlint before a new
additive immutable development commit. Dispatch only **`ios-ui`** and
**`consumer-core-io`** at that revision; verify actual `head_sha`, artifacts,
commands, named XML, source/runtime bindings and cleanup before updating scoped
issue progress. No SHA dispatch failure authorizes guessing a different ref or
repeating an uncertain POST.

The complete native/minimum-platform, IO parent ownership, Android hard-link/
SELinux-fixture,15 objc2-family legal gaps/SDK ambiguity, ordinary dependency
enforcement/trust, ABI and strict21-root packaged-consumer gates remain. A
partial consumer pass would narrow a blocker, not certify a release.

## Actual partial staging failure and exact root-build repair

After [full staged-source preflight016](evidence/ci-preflight-20261027-016/lead-review.json)
passes23 commands/1078 Python methods, strict MkDocs/actionlint, both whitespace
checks and eight actual HTML anchors with15591 held inputs, additive commit
`c5e14c9596760fca3a2493063b295161ce5e9d36` is pushed and both targeted profiles
are dispatched once. The owner-authorized all-actions/no-required-pinning/read
permissions, null Pages status, no releases and unchanged `main` are checked.
This preflight uses explicitly finite lightweight commands and owned tmpfs;
**no heavy-build8GiB guard is lowered**. Its archive follows the freeze, not
circular validation of future commits. Python counts overlap earlier runs.

[Consumer40480857516](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40480857516)
passes tooling, but actual producer Gradle exits **1/41.02s** before four
publication tasks or consumer execution. [Independent immutable Git/ZIP review](evidence/github-actions/40480857516/lead-independent-review.json)
verifies artifact12722503387,71891bytes, digest
`sha256:cc0092b58ca770aa495ea7ade34187373cb0bbee8d787f7ce4bd42eee2edb2cc`,
and all **737 selected inputs** against Git/before/after. All six independent
fixture-copy hashes match. There are **zero Kotlin consumer methods or XML**;
the unselected library job is intentionally skipped, not a skipped test.

Gradle init scripts also run in the included convention/plugin build. The
original adapter unconditionally resolves `:calf-core` there. The settings
plugin-resolution error wraps:

```text
Project with path ':calf-core' could not be found in project ':convention-plugins'.
```

This is an owning adapter-boundary defect, not a failed candidate-library method,
foojay version mismatch or reason to disable verification. Actual wrapper/Gradle
startup occurred and the controller's own lock is removed; no detached-daemon
cleanup attestation is invented. Original reports and bounded public diagnostics
remain. No source payload is substituted to make the consumer green.

The controller now passes a fixed `-Dnativecmpkit.partialStagingRoot=<canonical
producer checkout>`, **only to the producer**. The adapter validates an existing
absolute path and returns from every nonmatching build **before** any flag,
library or task lookup. The matching root additionally requires `nativeCmpkit`
identity; all four real publication tasks, exact file repository, version,
interlocks and seven-method independent consumer gates remain unchanged. A
name-only or inferred included-root selection is not accepted.

[Source-held red/green](evidence/partial-stage-root-binding-20261027/lead-review.json)
preserves36 controller methods/one failure and12 fixture methods/two failures;
corrected **48/48 Python methods** pass. All original and corrected source hashes
are rechecked. These are lexical/mocked tooling tests, **zero repaired Gradle/
Kotlin consumer executions**. New immutable `consumer-core-io` is required after
full staged-source preflight. Do not rerun the unchanged failed adapter or repeat
unrelated successful platform suites. UIKit40480810709 atc5e14c95 remains running
at this observation; no Apple result is claimed for it yet. Ledger and all
release/security/native/ABI/legal/full-consumer gates remain unchanged.
