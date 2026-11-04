# Native consumer606 — package-before-JNI and missing-three result contract

**2026-11-04; source-ready branch
`development/batch-native-consumer-next-20261104`, parent
`c06dac8477bb1b2029fdbe9f605627e7008a2f0e`.** This is the next related
#2 / BUILD-003, #38 / BUILD-004 and #3 / BUILD-006 verification patch, not
completion of any of those issues. The lead integrates and owns hosted
verification/issue updates. No dispatch, push, GitHub mutation or publication
occurred in this worktree.

## Confirmed ordering blocker and minimal change

The parent consumer's `tests/consumer/build.gradle.kts:198` configured native
desktop tests without a dependency on static package/native provenance checks;
the README's previous command invoked `desktopTest` before the separate static
checker. Missing package provenance/notice material could therefore be discovered
only **after** candidate JNI initialization. This is a verification-ordering
defect, not evidence that an untrusted binary executed or that native functionality
passed. The original fixture also had no integrated gate for running only the
three still-missing native methods with fresh, complete results.

The new build wiring at `tests/consumer/build.gradle.kts:211–293` adds:

- `verifyCandidateNativePackages`, depending on the unchanged
  `verifyCandidateResolution`, as a dependency of every desktop Test. It requires
  an independently supplied full producer SHA and absolute clean source checkout,
  checks its actual Git identity/status, then runs the existing source-bound
  checker with **all21 default roots** and this intended desktop/native host.
  No artifact-inferred revision, dirty diagnostic or reduced-module bypass enters
  the command. Static source inspection is not a project/composite dependency.
- Opt-in `nativecmpkitConsumerTestFocus=native`, desktop-only, with exactly the
  original three `PublishedNativeConsumerTest` methods. Default `all`, every
  original dependency, all four Kotlin files and all **17 original method bodies**
  remain unchanged. JNI checking, serial forks, staged/loaded-JAR binding,
  same-owning native resources and `finally` disposal of 100 valid handles stay.
- Invocation-specific UUID XML/receipt directories, disabled Test cache and
  UP-TO-DATE reuse, fail-on-empty selection/discovery, and the
  `verifyNativeConsumerResults` aggregate/finalizer. **Fresh Gradle DSL and graph
  qualification is recorded below; actual task-action ordering and failed/
  NO-SOURCE finalizer behavior still require execution.**
- Mapping from the existing host-selected JavaFX classifier to exactly the five
  intended native slots. Interpreter selection uses that same mapping, avoiding
  a new Darwin/Windows substring ambiguity. Windows ARM64 and musl stay unclaimed.

`verify_native_test_results.py:34–144` inspects one bounded, flat owning XML and
requires the exact suite/class plus three unique original method names and
`tests=3`, zero failure/error/skip. Empty, foreign, duplicate, nested/namespaced,
linked, oversized, malformed and DTD/entity reports refuse. The actual descriptor
is closed on success/refusal; held-file mutation checks remain bounded.
Preexisting receipts refuse. UUID/source/report consistency does **not** establish
builder authenticity, hostile directory-mutation protection or native behavior.
Its receipt explicitly reports method **counts in XML**, never native acceptance,
and keeps `release_readiness_certified=false`.

## Important new controls — first results retained, not replayed

| Original execution | Actual result | Scope |
|---|---|---|
| `important-first-next606.json/.txt` | **24 reported / 23 pass / 1 error**, unittest **0.023 s**, wrapper **0.193765 s** | NEW8 Gradle source controls + NEW16 synthetic XML/real filesystem/descriptor/CLI controls; six owning hashes held. No Gradle, Kotlin, JNI or native execution. |
| `failed-only-recovery-next606.json/.txt` | **1/1 pass**, unittest **0.001 s**, wrapper **0.138256 s** | Only the failed/changed UUID method. `uuid.UUID(None)` raised `TypeError`; the checker now catches it and this method also checks integer/Boolean invalid inputs. Two owning hashes held. |
| `REVIEW-source606.json` | **42 passive source/results checks** | Exact inverse of the two recovery fragments binds first hashes; the other23 accepted method bodies/inputs remain. Removing only90 added Gradle lines restores the parent byte-for-byte; original17, all104 nonowning consumer files and17 protected native/build/workflow/legal/helper sources stay. |
| `gradle-native-focus-dryrun606.json/.log` | **Gradle0 / 26.572274 s**, **112 inputs held** | ONE subsequently authorized actual offline Kotlin DSL/task-graph dry-run; all40 task actions SKIPPED, including compilation, resolution, package preflight and Test. Two inherited Compose runtime/foundation deprecation warnings retained; no candidate/JNI acceptance. |

Thus **24 unique controls are qualified by first accepted23 + failed-only1**,
not by a fresh24/24 suite run. The original failure remains failed and retained.
Private original hashes are recorded in `retained-originals606.json`; only the
known private worktree root is relabeled `<worktree>` in committed traceback text.
This sanitization is not a new execution. Parent accepted23+15, original17
consumer methods, prior reflective Kotlin compiler and hosted results were not
replayed. The changed Gradle file is **not** certified by that historical compiler
input map. `REVIEW-source606.json` predates the separate fresh dry-run; its zero
Gradle count records that review's scope, not a denial of the later execution.
`reviewer-refusals606.json` retains the first documentation classifier/count
refusals: a check label, not a private path, triggered an overbroad scan; the
not-yet-written documentation receipt also left the first staged count incomplete.
No source assertion or task result was weakened to repair that bookkeeping.

## Fresh configuration-only execution and still-unexecuted JNI

Before any heavy command the lead must grant the serial slot and preserve at
least8 GiB free; hosted-heavy reservations stay at maximum two **including queued**.
An unrelated project Gradle process was initially observed, so source/evidence
work continued without a heavy command. After its active command finished, the
lead granted this one bounded dry-run. Free space was **11,503,624,192 bytes
before / 11,499,139,072 after**, above8 GiB; the slot was released immediately at
termination. No heavy retry or native/Test action followed. Exact cached
Gradle9.7.1/Kotlin2.4.20/Compose1.12.0/AGP9.4.0 configured successfully offline;
complete consumer/target dependency resolution is **not** verified.

The **executed configuration-only** command used the existing, explicitly
unaccepted/incomplete stage directory. It supplied no manufactured producer
revision/root and did not execute preflight or JNI. The committed receipt relabels
only that private stage path; the original receipt/log hashes remain retained:

```sh
timeout --kill-after=10s 240s ./gradlew -p tests/consumer \
  verifyNativeConsumerResults --dry-run \
  -PnativecmpkitRepository="$EXISTING_UNACCEPTED_STAGE" \
  -PnativecmpkitVersion=0.1.0-preview.1 \
  -PconsumerTargets=desktop -PnativecmpkitConsumerTestFocus=native \
  --offline --no-build-cache --no-configuration-cache --no-daemon \
  --max-workers=1 -Dorg.gradle.jvmargs='-Xmx1536m -Dfile.encoding=UTF-8' \
  --console=plain
```

The actual graph ends with `verifyCandidateResolution` ->
`verifyCandidateNativePackages` -> `desktopTest` -> `verifyNativeConsumerResults`,
all SKIPPED under dry-run. This qualifies task names/types, the owning Kotlin
DSL/property wiring and an acyclic selected graph. It does **not** prove runtime
preflight success, JNI authenticity/functionality, real XML or cleanup/finalizer
execution. Build/settings/properties/source bytes stayed within the actual112
input map; the new evidence is separate and is not retrospectively that map.

Only after **genuine complete all21 metadata/desktop staged artifacts**, legal
notice/material/native manifests, independently reviewed clean producer Git/
source/input/output custody and host/toolchain dependencies exist may the lead
run the real missing-three command:

```sh
./gradlew -p tests/consumer verifyCandidateResolution verifyNativeConsumerResults \
  -PnativecmpkitRepository="$GENUINE_STAGED_REPOSITORY" \
  -PnativecmpkitVersion=0.1.0-preview.1 \
  -PconsumerTargets=desktop -PnativecmpkitConsumerTestFocus=native \
  -PnativecmpkitExpectedNativeRevision="$INDEPENDENT_REVIEWED_FULL_SHA" \
  -PnativecmpkitProducerSourceRoot="$INDEPENDENT_REVIEWED_CLEAN_PRODUCER_ROOT" \
  --no-build-cache --max-workers=2 --no-configuration-cache
```

An independent copied consumer must retain its build/settings/properties/source,
`verify_artifacts.py`, `native_license_supplements.py`,
`native_license_material_v2.py` and the new result checker. The independently
inspected producer root supplies the existing native contract/identity/legal
sources, not compiled project dependencies. Parent owns shared CI routes and
receipt integration. Do not wholesale-dispatch all five native hosts beyond
the two combined reservations or relabel a dry-run as package/native acceptance.

The real three-method run still does not establish ARM dialog cancellation,
glibc/Apple SDK minima, complete resource/leak/concurrency qualification or
full21/seven-coordinate/mobile/browser/Swift/API–ABI/dependency/legal/security
readiness. See the unchanged
[native producer plan](../native-package-provenance606/README.md). **No issue
closure is proposed; every release/package/deployment/Pages gate remains.**
