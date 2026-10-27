# Consumer metadata, cache containment and the actual UIKit alert crash

Single-agent, contained verification on `development/preview-hardening`.
**No issue is closed, no disposition is promoted, and no package, release,
deployment or Pages action is authorized by these results.** The ledger remains
87 implemented / 69 partially verified / 8 unresolved / 0 verified.

This is additive to the [preceding consumer/UIKit checkpoint](checkpoint-consumer-uikit-20261027.md).
Preserve its failures and the 164 original finding records. Earlier paragraphs
which say a run was running or that staging had not executed describe their
observation times, not the completed observations below.

## Actual UIKit delegate crash

[Run40480810709](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40480810709)
at immutable `c5e14c9596760fca3a2493063b295161ce5e9d36` passes tooling but fails
the genuine iPhone26.5 application suite. [Independent review](evidence/github-actions/40480810709/lead-independent-review.json)
reconstructs **715 selected inputs** from Git, matches both original input maps,
verifies the **94,381-byte** artifact digest, and recounts **82 executions / 81
passed / 1 failed / 0 skipped in15 XML reports**. Only one of11 mandatory
application methods is observed, and it fails; the other ten are absent.

Real activation reaches main Worker1/owned Worker2. The previous plist repair
is independently checked against the original C5 code: a genuine Boolean
`CADisableMinimumFrameDurationOnPhone=true` reconstructs the exact recorded plist
hash, and its earlier crash is absent. This is a verified manifestation of that
manifest change, **not a passing application suite**. Link/sign/install/owned
app stop/uninstall/absence/local-bundle cleanup succeed separately; transport
and the library suite remain failed.

The actual exception is:

```text
NSInternalInconsistencyException:
The presentation controller of an alert controller presenting as an alert
must not have its delegate modified
```

The stack identifies `AlertDialogManager.createController`. The development
implementation assigns `presentationController?.delegate` while creating an
Alert and also clears that UIKit-owned property in cleanup. The creation write
is exercised; the cleanup write is source-confirmed but not reached before this
crash. This is a **High-priority production regression in the development
implementation**, not a claim that the original upstream baseline had this
specific implementation or that a security exploit occurred. Related original
owners are UI-012/013/014.

### Owning repair and required verification

`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt`:

- Never assigns or clears Alert's UIKit-owned presentation delegate. Do not
  subclass `UIAlertController` or catch/suppress the native assertion.
- Assigns only ActionSheet's supported popover delegate; handles both its
  popover callbacks and compact/adapted presentation callbacks through one
  Main-confined reconciliation path.
- Reconciles exact native controller ownership and transition phase before
  emitting a user callback or releasing the presenter queue. Duplicate or stale
  callbacks cannot release a replacement owner. Disposal is terminal and not a
  user cancellation.
- Clears only a popover delegate whose native identity is still ours. The custom
  outside-tap recognizer remains limited to Alert, rather than competing with
  ActionSheet's native dismissal mechanism.

`NativeAlertLifecycleTest.outsideDismissRequestsAndDisposalRemainExactlyOnce`
adds a genuine application regression for repeated production dismissal entry,
terminal disposal, replacement ownership and cleanup. It calls the actual
production entrypoint, **not fabricated native touch events**. All three prior
alert methods remain. The application gate requires **12 named methods**, with
a synthetic receipt regression rejecting omission of the new one.

[Repair evidence](evidence/alert-delegate-repair-20261027/source-guards-green.json)
retains the seven-method source-guard red and corrected **7/7 lexical +26/26
synthetic receipt guards**. Actual fresh production/test KLIB and KGP application
model compilation passes **exit0/58.31s**, at **716 held source/copied inputs**;
[compile receipt](evidence/alert-delegate-repair-20261027/compilation/ui/receipt.json).
These are **zero executed native/library methods**. Later verification-tool
inputs differ, although the cited production/test bodies remain unchanged.
Fresh immutable application execution is mandatory. Actual outside gestures,
regular-width iPad/popover/rotation, accessibility, older supported OS behavior,
and broader action/disposal/presenter contention still need their own tests.

## Actual Core/IO staging and consumer DSL failure

[Run40486697786](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40486697786)
at immutable `d2b47840e352e0e04c3ae5c19d8b81b04fd967ab` passes tooling,
then fails the partial independent consumer job. [Independent review](evidence/github-actions/40486697786/lead-independent-review.json)
reconstructs **737 inputs**, matches before/after, checks all six independently
copied fixture hashes and verifies the **81,312-byte** artifact digest.

- Actual producer Gradle passes **exit0/244.08s**. All **four** Core/IO root+
  desktop publication markers execute. There are150 staged files/323,460 content
  bytes,20 static artifact-hash bindings and **308/308 partial static checks**.
  Thus the preceding exact producer-root binding repair actually executes.
- The independent child fails **exit1/19.01s**, before resolution or tests:
  `build.gradle.kts:20:32 Unresolved reference 'io'`, `:40:23 'security'` and
  `:49:61 'it'`. There are **zero resolution receipts, consumer methods or XML**.
- Kotlin's JVM-plugin `java` extension receiver shadows package-qualified
  expression references. Both partial and full consumer scripts now explicitly
  import `java.io.File` / `java.security.MessageDigest`, preserving type binding
  without toolchain downgrade, insecure TLS or dependency substitution.
- The review tool's own first incorrect five-part group-path assertion is
  preserved beside the corrected four-part-group review. It is not a producer
  failure and no check was waived.

The separate [local immutable D2 attempt](evidence/consumer-core-io-local-d2b47840-20261027/lead-independent-review.json)
fails producer Gradle **exit1/478.50s** after both Core tasks, while downloading
three exact IO/coroutine JARs with TLS-handshake termination. Its737 inputs and
six copied files hold; zero consumer methods/XML. Preserve that network failure.
The earlier owned dirty6eb staging was atomically relocated, preserving1425
files/4,308,327 content bytes and all inode/hash identities. The failed local D2
attempt leaves75 Core-only files in `build/verification-repo`; preserve/relocate
them before a new local controller run. Do not delete unrelated caches.

Actual copied standalone Kotlin DSL `help` subsequently passes **exit0/19.773s**
at741 held inputs, using JDK17/Gradle9.7.1 and normal official dependency
acquisition. Its earlier offline attempt fails **exit1/19.414s** on an uncached
`error_prone_annotations:2.27.0` JAR. [Both receipts](evidence/consumer-metadata-cache-repair-20261027/dsl-help002/receipt.json)
are retained. `help` compiles/configures the repaired script, **does not resolve
candidate dependencies or execute any of the seven methods**, and reuses the
private producer plugin home only for this explicitly non-consumer diagnostic.
It is not the fresh-cache consumer run below or a full21-root DSL certificate.

## Metadata labels and candidate cache containment

### Actual Gradle contract, not a production identity rewrite

A real Gradle9.7.1 file-Maven probe retrieves canonical nativeCmpkit bytes but
resolves/caches them under the GMM `files.name`:

```text
files.name = calf-core-desktop-0.1.0-preview.1.jar
files.url  = nativecmpkit-core-desktop-0.1.0-preview.1.jar
```

The resolved and staged Core JAR share SHA256
`edfeec3fec4f6099b8140819d7cb07933f0afc0c7d470accc640502ec46f11a4`.
The initial probe's variable-shadowing failure and the subsequent driver's
incorrect filename/path assumption are retained in the
[probe evidence](evidence/file-maven-cache-probe-20261027/additive-review.json).
The corrected probe Gradle command exits0/9s; that does not turn the original
orchestration assumption into success or execute consumer methods.

Retained Calf Gradle project names explain the display label. A display name is
not the Maven URL or old-group fallback. **Repair the verification fixture's
assumption, not production identity merely to appease it.** Public package,
framework/JNI names, coordinates, authorship and license remain unchanged.

Both `tests/consumer/{build.gradle.kts,io-desktop/build.gradle.kts}` now share an
identical `bindCandidateArtifact` body. It requires a known publication root/
target suffix, exact version/group, actual primary metadata-declared filename,
canonical nativeCmpkit URL, exact root metadata/back-pointer, and staged/
resolved size+SHA256 identity. Only the explicit native/retained label for that
coordinate is eligible. Arbitrary labels, sources, traversal, other groups,
project/class-directory substitution or fallback are not accepted. Full-matrix
transformed/native/minimum-platform behavior remains unverified and fail closed.

The partial resolution schema is now **v2**. Candidate rows explicitly bind
`staged_file`, `metadata_file`, `metadata_sha256`, `declared_file_name` and
`declared_file_url`; third-party rows retain their original identity fields.
`scripts/ci/core_io_consumer.py` independently re-reads the held target metadata,
checks both API/runtime primary declarations, their exact candidate-root link,
hash and bytes, then validates all **four classpaths** against those bindings.
Runtime class-origin assertions still require the exact loaded JAR/hash; **all
seven methods and both XML reports remain mandatory**. The six IO method bodies
are byte-identical to the original full consumer. The full21-root gate is not
shrunk or certified by the partial fixture.

### Conditional cache-export risk and owning boundary

The probe actually creates the candidate payload group under Gradle `modules-2`.
The earlier controller shared its dependency home between producer and consumer.
A **future successful** child could therefore cause unverified own candidate
JARs to be saved by the dependency-cache action. **All prior consumer jobs failed;
no such candidate cache upload/leak was observed.** This is a demonstrated cache
path plus a conditional export risk, not a proven disclosure/exploit.

The consumer now has fresh `consumer-gradle-home`, `consumer-user-home` and
temporary directories under its confined output, never the cached producer
home. No live producer cache is mounted as a read-only dependency cache or copied
into the child. Known candidate payload/descriptor group paths in producer
`modules-2` must be absent before and after execution. Unexpected data is
preserved, the job fails and no cache-save eligibility is granted. Original
staging and copied-fixture bytes are captured even when consumption fails;
fresh XML observations remain available without promoting a failed candidate.
This is **not an OS sandbox**, ordinary dependency-trust review, or a detached
Gradle/descendant-cleanup attestation. Those gates stay open.

## Efficient verification cache policy

`scripts/ci/dependency_cache_inputs.py` selects exact configured root/project/
sample/convention Gradle inputs, active Cargo/lock/config files, stored Yarn
inputs and the relevant controller/runtime/consumer recipes. Its content digest
excludes the observed commit SHA, unrelated source/tests, old archive build files
and project outputs. New/modified declared dependencies, locks, toolchain or
recipes invalidate the key. Included-project discovery fails on unsupported
settings syntax; missing, linked or oversized selected inputs fail.

The active workflow uses **v2 exact dependency +actual compiler/runtime +OS/CPU/
slot/suite/module-selection keys**, with no broad restore prefixes. The two-root
cache selects **producer** wrapper/modules-2 only; the fresh consumer home and
staged packages are not cached or uploaded. Caches still contain untrusted
third-party dependency observations, never reused XML/library-test outcomes or
release provenance. All actions remain allowed/no mandatory SHA pinning,
verification tokens remain read-only, checkout credentials do not persist,
manual profiles are bounded, and no publishing/deployment step is added.

Synthetic tests cover metadata alias/URL/hash/type/root/duplicate-key/variant
tampering, all classpaths, missing cases, preexisting homes, candidate cache
appearance and final failure captures; lexical tests enforce identical fixture
binding and real loaded-class checks. Scoped pass counts overlap the previous
53-method model run and prior13-method fixture guards; they are not additional
native or independent packaged executions. Full source-held preflight and fresh
immutable `ios-ui` / `consumer-core-io` results must be recorded separately.

## Source-held staged preflight018

[Independent readback](evidence/ci-preflight-20261027-018/lead-review.json)
recounts **23/23 commands and1,122 Python tooling executions**, with all
**16,070 captured inputs and the staged index held**. Both worktree and staged
whitespace checks, strict MkDocs, actionlint, migration integrity, baseline audit,
resolution indexes and generated resources pass. Twelve anchors are checked in
nine distinct actual HTML output files, including this checkpoint. Root capacity
is measured above8GiB before/after, not inferred from the older incorrect prose;
the finite lightweight run lowers no heavy-build reserve. These counts overlap
prior tooling runs and include **zero native/library/packaged-consumer methods**.

The lossless archive and this additive paragraph follow the freeze, not circular
validation of a later commit. Production, consumer and workflow inputs remain the
held repair inputs; fresh immutable `ios-ui` / `consumer-core-io` execution and
independent outcome/ownership review remain required. No issue or release gate
is promoted by preflight018.

## Remaining release gates and next work

No current result lifts native/device, full21-root/7-coordinate/minimum-platform
consumer, ABI, legal, dependency-trust or release gates. IO-023 native parent
lifetime/Main affinity, the actual Android hard-link SELinux denial,15 objc2-family
license-material gaps/SDK ambiguity, ordinary dependency/descendant ownership,
cross-host native payload completeness and API/consumer compatibility remain.
Follow [release readiness](release-readiness.md), not a successful partial build
badge. Re-run only changed profiles at an exact development commit; inspect raw
fresh counts, absent methods, hashes and cleanup before adding issue progress.
