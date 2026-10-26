# Unchanged legacy JVM binary fixture

**Baseline sanity and two local-JAR candidate diagnostics executed; staged Maven
artifact execution remains pending.** The
[baseline-only receipt](../../../docs/development/evidence/legacy-binary-baseline-sanity-20261024T195518Z/README.md)
records six cases / 31 assertions on clean old JARs. The [paired local evidence](../../../docs/development/evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md)
records the same six cases / 31 assertions on each actual local candidate, with
unchanged class hashes and dependency bytes. This is separate from the still
unexecuted strict Kotlin Maven consumer and is not whole-API or release proof.

`LegacyBinaryConsumer.java` contains six narrow JVM linkage cases / 31 expected
assertions: IO constructor/extension owners, picker factories and an external
default-interface implementor, permission/status constructors, share result/value
types, WebContent/Cookie signatures, and old inlined icon constants compared with
the candidate's runtime fields. It deliberately does not open UI/native dialogs.
It does not exhaustively check Kotlin default arguments, metadata or inline
bodies, Compose lowering, Android, JS/Wasm, KLIB or Swift ABI.

The runner:

1. Validates the clean detached baseline HEAD, all 21 published baseline desktop
   JAR hashes and the independent source-bound `javap` inventory.
2. Rechecks **every byte file** named in the candidate's successful static artifact
   report; every one of the 21 staged desktop JARs must be included.
3. Rejects a supplied third-party JAR containing `com/mohamedrejeb/calf/` or `jodd/`
   fallback classes. There is no network, `mavenLocal`, producer compilation or
   project substitution.
4. Calls JDK `javac --release 17 -proc:none` exactly once against **baseline JARs**
   plus explicit third-party dependencies. Two class outputs are hashed.
5. Runs those unchanged outputs first against baseline JARs (fixture sanity),
   then against **candidate JARs**, keeping third-party dependencies unchanged.
   It rechecks the two class hashes before/after both executions and rejects
   missing/zero/unexpected case counts.
6. Saves commands, JDK versions, bounded output/exit evidence, source/tool/input
   hashes and the exact class inventory in a new directory. Old receipts are not
   overwritten. A failure leaves its evidence; do not delete it to imply success.

After candidate staging/static inspection and lead build scheduling, from the
repository root:

```sh
python3 tests/consumer/binary_linkage.py \
  --baseline-root /tmp/nativecmpkit-release-baseline-94d2492e \
  --repository "$PWD/build/verification-repo" \
  --artifact-report build/consumer-static-linux.json \
  --version 0.1.0-preview.1 \
  --dependency "kotlin-stdlib-2.4.20=$KOTLIN_STDLIB_JAR" \
  --javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac \
  --java /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
  --output build/legacy-binary-consumer-run-1
```

`KOTLIN_STDLIB_JAR` must be the inspected absolute public dependency JAR from the
supported consumer toolchain, not a guessed cache hit. Supply additional actual
third-party runtime JARs with repeated `--dependency identity=/absolute.jar` if
the narrow fixture requires them. Their exact hashes are recorded; they must not
be changed only on the candidate side. Adapt JDK/worktree paths explicitly on a
different trusted host. The runner intentionally refuses a missing baseline or
incomplete artifact inspection instead of silently compiling against new APIs.

Even a successful run reports `binary_compatibility_certified=false` and
`release_readiness_certified=false`: six actual linkage cases are useful evidence,
not certification of every API, supported platform or native operation. Python
unit tests for the runner's receipt helpers never execute Java and are separately
classified as synthetic tooling coverage.

## Separate contained local-JAR diagnostic mode

Missing native dependency legal material currently prevents distributable
candidate staging. Do **not** disable that gate or fabricate a successful static
artifact report to get linkage feedback. The runner instead has an explicitly
different, non-distribution mode for lead-scheduled **locally built JARs**:

```sh
python3 tests/consumer/binary_linkage.py \
  --baseline-root /tmp/nativecmpkit-release-baseline-94d2492e \
  --diagnostic-local-root "$PWD" \
  --diagnostic-jar-inventory build/local-jar-diagnostic-inventory.json \
  --dependency "kotlin-stdlib-2.4.20=$KOTLIN_STDLIB_JAR" \
  --output build/legacy-binary-local-diagnostic-1
```

This mode rejects `--repository`, `--artifact-report` and `--version`; its result
is labeled `mode=local-jar-diagnostic`, `distribution_verified=false` and
`maven_artifact_inspection_passed=false` even if the Java cases pass. It does not
run the standalone Gradle/Maven consumer, inspect publication metadata/notices,
load native libraries, or satisfy artifact-consumer/release gates. It is still
baseline-compiled old bytecode running on real local JARs, not stubbed classes.

The inventory is a local JSON object with **exactly** these keys:

```json
{
  "schema_version": 1,
  "mode": "local-jar-diagnostic",
  "distribution_verified": false,
  "source_revision": "FULL_40_HEX_BASE_COMMIT",
  "source_tree_dirty": true,
  "build_receipt": {"path": "relative/build-result.json", "bytes": 123, "sha256": "EXACT_SHA256"},
  "source_input_receipt": {"path": "relative/build-inputs.json", "bytes": 123, "sha256": "EXACT_SHA256"},
  "source_verification_receipt": {"path": "relative/build-verification.json", "bytes": 123, "sha256": "EXACT_SHA256"},
  "jars": [
    {"artifact": "nativecmpkit-core-desktop", "published_module": true,
     "path": "calf-core/build/libs/ACTUAL_LOCAL_JAR.jar", "bytes": 123, "sha256": "EXACT_SHA256"}
  ]
}
```

Placeholders illustrate the schema, **not a passing inventory**. Supply all 21
published desktop identities exactly once; optional unpublished JAR records are
hashed but never added to the published linkage classpath. Bind to the actual
producer command's inspected exit-zero result and unchanged-source verification,
not an unrelated successful test or an overall failed command containing some
successful tasks. The source-input receipt must have the matching `base_commit`
and a nonempty `files` map of relative input paths to actual SHA256 values. The
source-verification receipt must say `exit_code=0`,
`input_hashes_unchanged=true`, `changed_inputs=[]`. All named receipt/JAR/input
bytes are rechecked against the selected root, and HEAD/dirtiness must match.
Tracked and untracked source changes are deliberately not called a clean commit.

The lead's capture must include the relevant source/build/resource/native inputs,
and report its omissions honestly. A hash list cannot prove that a build consumed
exactly those files or that every relevant file was captured. The runner therefore
does **not** convert a supplied receipt into an immutable/reproducible-build
attestation. It rechecks source/runtime/fixture/receipt bytes during its own
bounded executions, preventing an observed concurrent mutation from appearing as
stable evidence. Use `jvm_abi.py snapshot/compare` on the same inventoried JARs
for the broader diagnostic delta; classify public/internal deltas rather than
treating six passing cases as complete compatibility.

**Actual local diagnostics:** the [first 700-input/23-JAR iteration](../../../docs/development/evidence/jvm-diagnostic-20261024T223018Z/README.md)
passed this six-case fixture but its broader raw JVM scan failed 19 removals. A
separate unpublished-geo Java field/source probe confirmed private-access and
reflection failures that this published-module fixture cannot cover. The
[second 701-input/23-JAR iteration](../../../docs/development/evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md)
passed this fixture again and verified the minimal geo repair with the **original
baseline-compiled failing field class**, plus separate fresh source compilation.
Only geo's JAR changed. The raw scan still exits1 for 18 source-classified
internal/generated/modifier records; the original failures were not overwritten.

Both pre/postchecks passed, after which their source freezes were released. The
preserved exact local JAR/source snapshots, receipt/tool hashes and own compiled
Java class ZIPs distinguish those historical runs from later source changes.
All distribution/Maven/native/release flags remain false. Six cases repeated on
two iterations are not 12 distinct test methods, and Python tooling tests are
never counted as these actual Java executions.
