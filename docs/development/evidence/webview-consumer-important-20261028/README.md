# Packaged WebView consumers and publication recovery — 2026-10-28

## Direct original-criteria closure — 21:31 UTC

**BUILD-001 / [#1](https://github.com/Apdelrahman1911/nativeCmpkit/issues/1) is
readback-closed/completed.** All three original requirements were reviewed before
closure; see [criteria review](direct-closure/criteria-review.json) and
[final comment readback](direct-closure/comment-final-readback.json).

- Linux x64 [40766415004](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40766415004),
  immutable `a0eba4ef`: **4/4**, two fresh XML, whole workflow SUCCESS; staging
  0/287.08s, module consumer 0/72.02s, POM consumer 0/71.02s. All836 own-Git inputs,
  actual JDK17 daemons, staged artifacts, isolated fixture copies and candidate-free
  producer cache held. [Accepted review](coordinate-native002/accepted-review.json).
- Both macOS architectures and Windows x64 in
  [40768437205](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40768437205),
  immutable `71ed2c3b`: **4/4 each**, two fresh XML per host, each required host job
  SUCCESS. All837 own-Git inputs/JDK17/staging/fixture/cache held. Reviewed receipts
  are in `remaining-native001/{macos-arm64,macos-x64,windows-x64}/accepted-review.json`.
- **16/16 target-mode-method executions**, two authored methods/eight XML, zero
  failures/errors/skips. Real public Compose/JFXPanel/WebEngine, exact loaded
  staged-JAR origin/hash, Unicode HTML, typed JS and native disposal passed.
  Actual POM/module dependency selectors equal across all four required hosts;
  191/191 static checks per host. The preserved exact-version classifier registry
  observation covers six modules × five advertised classifiers,30/30 HTTP200.
  Sixty directly owning current source/docs files match the accepted inputs.
  Accepted successful tests were not replayed.

**Retained additional limitation:** Linux arm64 in40768437205 FAILED during
producer staging, exit1/162.05s, unknown `Check failed`, **zero consumer tests/XML**.
Its selected bounded diagnostics do not establish the cause. The whole workflow
remains FAILED. This extra host was not an original native-launch criterion; no
Linux-arm64 native pass is inferred. Strict stage checks now have explicit contract
messages and producer stacktraces retain bounded failure locations/causes; local
configuration 0/34.01s/838held inputs and37 synthetic guards pass, zero native tests.
Only the failed host is dispatched in
[40772821771](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40772821771)
at `8a2a46e6`; results remain pending here. See `arm64-diagnostics-native001/`.
CI/release gate #3/BUILD-006 remains open. No registry publication, release,
complete21-root, minimum-platform, ABI, legal or dependency/security certificate.

## Additional ARM producer failure reviewed — 21:54 UTC

[40772821771](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40772821771)
at immutable `8a2a46e6` is now reviewed **FAILED**: stage exit **1 / 161.04 s**,
all 839 own-Git input hashes match and hold, `selected=[]`, **zero consumer
methods/XML**. The whole workflow is failed. See
[failed review](arm64-diagnostics-native001/failed-review.json) and
[dependency explanation](arm64-diagnostics-native001/dependency-host-publication-explanation.json).

Exact KGP2.4.20 bytecode disables all default KMP publications on an unsupported
Kotlin/Native producer host when any native target is declared. Linux ARM64 is
not a Kotlin/Native producer host; desktop-only staging selects publication tasks
but retains iOS declarations. This explains the actual missing tasks, not a
JavaFX crash. The actual internal branch/diagnostic text was not captured on this
runner. The explicitly internal override, fabricated publications, target pruning
and candidate-JAR uploads were not used. A supported producer retaining exact
metadata is still required for the extra ARM consumer. #3 stays open; #1's four
original accepted hosts/closure are unaffected and were not replayed.

## Historical owning coordinate recovery checkpoint

**#1 stays open.** [Five-host attempt40756542697](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40756542697)
at immutable `f9f6631e` remains FAILED, **zero evidenced consumer methods/XML**.
The [independent failure review](recovery001/independent-failure-review.json)
checks all five artifacts and all834 own-Git inputs. Linux x64 staged both real
publications but static191 checks have eight failures: unbuildable Apple target
redirects still use Calf artifact names. macOS x64/arm64 each pass191 static
checks and have equal dependency-selector documents, but their module consumers
fail before the fresh test marker; POM consumers are not reached. Linux Arm
producer and both macOS child causes are unknown because the actual child logs
were neither uploaded nor printed. Windows fails its `bin/java` preflight before
producer execution; the actual executable is `java.exe`.

The owning publication convention now normalizes only exact old target module/
URL pairs in the public metadata-generation task. KGP creates **no** publication
for unavailable local-cinterop targets; its fallback uses the retained Gradle
project name. Eager renaming interfered with Vanniktech; deferred container
renaming either accessed the wrong extension or left these absent targets
unchanged. All three attempts are preserved in `coordinate-after001/002/003/`.
See [ADR0009](../../../decisions/0009-publication-coordinate-normalization.md).

- `coordinate-after004/`: actual generation exit0/34.01s. Only the eight Apple
  module/URL pairs change; all desktop JSON and other root fields remain equal.
  The initial readback wrapper wrongly required optional `createdBy.gradle.buildId`
  and raised KeyError. A separate exact original-JSON comparison succeeds without
  ignoring any field and without rerunning Gradle; the wrapper error is retained.
- `coordinate-final001/`: after extracting the owning finite schema and adding
  actual Kotlin regressions, **6/6** JUnit methods, one fresh XML, plus actual
  generated root/desktop metadata match the accepted corrected JSON; exit0/61.01s,
  held836 inputs/JDK17. This is the dirty `79861d7c` source whose owning changes
  were subsequently committed as `b3be6dfd`, not consumer/native execution.
- `coordinate-tooling002/`:101/101 synthetic metadata/consumer/classifier/JDK/
  diagnostics/cache guards; includes earlier15, not cumulative unique counts.
  They do not validate the failed Kotlin helper iterations.

Bounded compiler/task/cause diagnostics now retain public child errors, not full
logs/environment. Windows explicitly selects `java.exe`; source/JDK/classifier/
metadata/cache and permissions gates are not relaxed. Source repairs are pushed
at immutable `b3be6dfd128890d5523621c7ff79f35f0fa5cfdf`.
**Linux x64 recovery40763811423 is independently reviewed FAILED** in
`coordinate-native001/`: two actual local publications pass0/224.07s and
static191/191 passes, but independent `compileTestKotlin` fails1/129.03s at
`ComposePanel.dispose()` (OPT_IN_USAGE_ERROR). All836 own-Git inputs, staging,
fixture copies and actual JDK17 are held; **zero consumer methods/XML**, POM
mode not reached. This is a fixture compile blocker, not an executed native
WebView failure. The actual Compose1.12.0 JAR marks only this cleanup method
`ExperimentalComposeUiApi`; narrowly opt in without removing disposal. Repair
`a0eba4ef` has only that fixture change. Linux-only recovery
[40766415004](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40766415004)
is dispatched once (`coordinate-native002/`), results not yet accepted at this
checkpoint. Successful Core/IO and unrelated/native suites are not replayed.
Cross-host native launches and both metadata modes remain required before #1
closes. No release or registry publication.

## Historical preparation checkpoint

The original preparation statements below describe their earlier checkpoint,
not a later run's result.

**BUILD-001 / [#1](https://github.com/Apdelrahman1911/nativeCmpkit/issues/1)
remains open. No packaged WebView test has executed in this checkpoint.**

The new independent [`webview-desktop`](../../../../tests/consumer/webview-desktop/README.md)
fixture stages only the WebView metadata/desktop publications, once per host,
then resolves/runs two public tests in each of two separate fresh consumer trees:
Gradle module metadata (root coordinate) and POM-only (explicit desktop
coordinate, with metadata redirection disabled). It never substitutes producer
classes/projects/internal owners or the existing sample. Runtime origin checks
bind the actual loaded JAR to held staging and its exact metadata display-name/
Maven-URL/hash mapping; POM resolution's canonical filename is recorded distinctly.

Public Compose WebView is mounted in a real Swing window/JFXPanel, loads Unicode
HTML, evaluates object/null/undefined/throwing JavaScript and releases its native
embedding owner. Tests fail on unavailable/headless/native conditions, rather
than using assumption skips. The consumer explicitly requests all six aligned
JavaFX21.0.13 host classifiers. The five-host matrix covers Linux x64/arm64,
macOS x64/arm64 and Windows x64, with bounded two-way concurrency and finite
failed-host recovery profiles. Verification permissions remain read-only.

## Actually inspected preparation outcomes

- `configuration001/`: offline Gradle configuration **FAILED** on uncached
  `error_prone_annotations:2.27.0`, exit1/14.00s, actual JDK17 and held inputs.
  No build-script or runtime pass follows.
- `configuration002/`: normal acquisition/configuration **PASS**, exit0/21.01s,
  actual JDK17 and held inputs. `help` executed; **zero Kotlin library/consumer
  runtime tests**. The pre-existing Core/IO staging directory was only a required
  directory parameter and was **not consumed or changed** by this configuration.
- `tooling001/`:16 methods, one error: duplicate XML correctly rejected by the
  existing parser, but the synthetic fixture expected a narrower exception.
  Original XML is now saved before parsing; invalid duplicates still fail closed.
- `tooling002/`:16/16 focused synthetic methods pass, not native/runtime tests.
- [40754502594](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40754502594),
  immutable `dacc5567`, **FAILED before any consumer job**. The577-method CI
  tooling suite had one old whole-workflow cache-count assertion expecting two
  keys; this new separately scoped producer adds the third exact key. No comma
  selector was put into a key. All consumer jobs were skipped, zero native tests.
  Initial dispatch visibility lag was reconciled read-only, not redispatched.
- `cache-recovery001/`:85 selected owning tooling methods pass with held834
  inputs on the dirty precommit repair. The exact three-key assertion and the
  no-raw-comma selector checks remain; no cache/input/consumer gate was relaxed.
  This85 includes the earlier16/45/9 selections; do not sum them as unique tests.

The original successful7-method Core/IO consumer is not replayed or generalized.
Old `build/verification-repo` is preserved. Candidate data in the known producer
cache group fails instead of being deleted/exported; separate child Gradle/HOME/
tmp are uncached. Only JSON/original XML evidence, not packages or private/full
job logs, is uploaded. No full21-root/API/ABI/minimum-platform/dependency trust/
legal/security/release gate is cleared. Cross-host generated dependency-selector
comparison and actual consumer runtime review are still required before #1 closes.
