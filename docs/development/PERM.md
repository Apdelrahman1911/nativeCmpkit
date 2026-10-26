# Permissions implementation after the audit

Scope: **PERM-001–017 and PERM-024**, after the lead's upstream synchronization
completion on 2026-10-24. Geo (PERM-018–023) is owned separately; see [GEO](GEO.md).
The immutable [baseline findings](../audit/findings/PERM.json) and baseline
reproductions are preserved. This document describes current source changes, not a
claim that iOS/Android device behavior was verified.

## Compatibility decision

Keep `Permission(name)` equality, all 28 built-in extension properties, public
packages, both factory signatures, mutable `PermissionState.status`, and the exact
`Granted`/`Denied` sealed status cases. Existing exhaustive `when` statements remain
valid. Keep `AndroidPermissionMapping`'s original four-argument/default constructor.
The internal duplicate expect/actual aggregate classes become one common aggregate;
public interfaces do not acquire required methods.

Add `PermissionDetails`, the optional `PermissionDetailsProvider`, and the
`PermissionState.details` extension. Details separate availability, usable access,
requestability, last explicit request outcome and a narrower native capability.
Third-party states without a provider report Unknown rather than inventing metadata.
On iOS an optional `PermissionSnapshotHelper` and lifecycle hooks coexist with the
unchanged `PermissionHelper` interface. Existing explicit Granted/NotGranted helper
methods are retained. No source/ABI compatibility certification is implied by these
intentions; the consumer fixture and target builds are separate gates.

Intentional behavior corrections:

- Unknown/invalid Android registration is no longer a grant. Empty native strings
  require explicit `alwaysGranted = true`; SDK-filtered/explicit no-gate entries
  retain the legacy grant, with **NotRequired**, not unrestricted operation access.
- Duplicate logical input identities become one member. Bulk callbacks contain all
  requested identities, including aliases, unsupported and no-gate entries. Empty
  batches complete. Single-member launches still return that member's map.
- iOS FineLocation no longer advertises precise authorization for reduced accuracy;
  CoarseLocation remains usable with Approximate details. There is no automatic
  temporary-full-accuracy purpose-key request.
- iOS limited Photos/Contacts authorization is usable with Limited details, never
  reported as full item access. Modern WriteCalendar requests/accepts write-only
  scope, while ReadCalendar may request a full-access upgrade. Older EventKit only
  offers legacy shared event access.
- Unsupported desktop/web requests complete false, rather than silently hanging or
  blanket-granting macOS/browser capabilities. Portable settings navigation is not
  implemented for these unsupported targets.

## Request execution and ownership

### Android

`AndroidPermissionRegistry` validates entries and synchronizes access. Register
custom entries before creating states. A request snapshots mappings by requested
logical identity; results never use a process-global first-match reverse lookup.

`AndroidPermissionRequestPlan` deduplicates native strings, includes coarse with
fine on API 31+, and derives results for **every requested logical identity**.
`AndroidPermissionRequestRunner` drives foreground then (only API 29, after a
foreground grant) background stages. A background-only request never escalates
foreground implicitly. API 30+ background requests report prerequisites/settings
requirements; the application must explain the need and explicitly offer
`openAppSettings`. Android selected-media access is supplemental Limited metadata,
not a false full media grant. Rationale=false alone cannot identify permanent denial.

State bindings use updated callback holders and state-keyed ActivityResult
registrations. Requests coalesce on the same owner; aliases refresh before results.
Resume refresh includes previously granted states. Disposal releases ownership and
ignores stale results. Process recreation restores OS permission observations, not
an application callback from a dead composition. Concurrent unrelated state owners
should be grouped instead of launching overlapping system requests independently.

### iOS core

`CallbackPermissionState` is the production state owner, not a test-only copy. It
creates helpers and runs native requests, observations, settings and state delivery
on the supplied dispatcher (Main.immediate in the iOS factory). Tests inject a
backend and scheduler; they do not impersonate CoreLocation/Photos/etc.

The controller invalidates older observation generations, coalesces overlapping
requests, ignores duplicate native results, refreshes a coherent snapshot before
application callbacks, releases ownership before reentry, handles query failures,
and suppresses all delivery after disposal. Non-cancellable Apple authorization
prompts may remain visible; suppressing callbacks does not dismiss OS UI.

`PermissionBatchRequest` serializes one request at a time, handles synchronous
already-authorized/empty cases without recursive stack growth, and emits one full
map. Siblings expose their own single-request callbacks without turning a bulk
request into a sequence of partial maps. Lifetime cancellation drops a disposed
owner's pending callbacks instead of fabricating user denial.

### Native feature adapters

| Finding | Current source treatment | Remaining platform verification |
|---|---|---|
| 009/010 | WhenInUse can explicitly request Always; NotDetermined/unknown and unchanged initial upgrade events are nonterminal; clear pending callback/timer before invocation; dispose delegates; 60s timeout | Actual OS dialog order, Allow Once, deferred Always upgrade/decline, multiple scenes and permission revocation |
| 011/012 | Pure calendar request/access policy, retained EventKit store, guarded iOS17 APIs, modern full vs write-only requests and usage keys | Minimum supported iOS, missing-key behavior and real calendar grant/upgrade matrix |
| 013 | Passive Wi-Fi/local-network observations; explicit active-app/configuration-checked Bonjour probe; Kotlin adapter strongly owns a separate NSObject protocol delegate; common request owner cleans adapter/timer before callback; failures/timeouts are not denial | Real local-network prompt/probe semantics on physical devices; it is a heuristic, not a definitive authorization-query API or Wi-Fi configuration API |
| 014 | Kotlin request adapter strongly retains its separate NSObject delegate and manager; polls undetermined authorization until result or 60s timeout; identity-local cleanup and disposal | Weak-delegate/device behavior, powered-off/Bluetooth reset, prompt delays and memory instrumentation |
| 015 | Existing and fresh eligible notification authorization share the APNs registration-before-callback path on Main | Entitlements, APNs delegate token/error delivery and actual push behavior (never promised by the Boolean result) |
| 016 | Passive restricted/unknown/limited/precision/provisional/ephemeral metadata; modern Photos access-level query; limited contacts handling | OS-version-specific privacy matrices and browser/desktop backends remain separate |
| 024 | Remove all-files manifest guidance; document legacy API boundaries, scoped storage, SAF/MediaStore and special-access separation | Device storage workflows and distribution policy review |

Notification/calendar/contacts asynchronous helper-owned state is marshalled to
Main. Registry factories are invoked outside the iOS registry lock. The library's
permission result is never a guarantee of a successful protected operation.

## Live application configuration

Use [the current permission guide](../permissions.md), not baseline audit snippets.
The sample owner separately removed unnecessary SMS/all-files declarations and
added modern calendar/Bonjour keys; those edits are configuration evidence only,
not a permission-device test. The modular feature dependencies and Apache/upstream
notices are unchanged. No package was published by this area owner.

## Tests and evidence

Tests live in the **library modules**, not the sample. Current source contains:

- core: 21 common tests covering production gate/batch/controller/aggregates and
  unsupported outcomes, plus three shared Compose-runtime recomposition scenarios
  with non-Android and Robolectric Android runner wrappers (24 cases per target);
- core Android host: 12 tests covering the actual registry/planner/runner with
  explicit SDK/OS-grant inputs, aliases, empty/all-filtered batches, cancellation,
  stage ordering, prerequisites and selected-media scope; these are plain JVM tests;
- five additional Android-host tests exercise the public Android factories, real
  Compose/ActivityResult contracts, callback replacement, alias/empty batches,
  lifecycle revocation, disposal and changed permission identities under Robolectric;
  they intercept OS launches and do not show device permission dialogs;
- feature modules: 48 common functions, including real production local-network
  and Bluetooth request-owner tests with injected native/timer adapters, and
  exhaustive authorization/request policy cases in every feature module.

These are **89 distinct source test scenarios**, with **92 annotated test-function
declarations** because the three shared scenarios have two platform wrappers.
There are 72 permissions desktop cases and 41 core Android-host cases. The dated
receipts below separate which targets ran in each command; the 24 common core
scenarios run on both targets, not as different logical tests. None of these counts
is a device-test count.
The lead schedules every Gradle invocation. Suggested focused rerun commands (the
actual combined desktop invocation is recorded in the dated receipt below):

```sh
./gradlew :calf-permissions:calf-permissions-core:desktopTest \
  :calf-permissions:calf-permissions-core:testAndroidHostTest \
  --max-workers=2 --no-configuration-cache
# Repeat desktopTest/jsBrowserTest/wasmJsBrowserTest for each feature Gradle project.
# macOS/Xcode: compile each iOS module and run iosSimulatorArm64Test, then device fixtures.
```

[First desktop receipt](evidence/PERM-desktop-first.json): **18 interim core tests**
executed with zero failures/errors/skips on 2026-10-24, against the source hashes in
that receipt. The combined root command exited **1** due to separate navigation/UI
compile errors; it must not be reported as a successful combined build. Subsequent
desktop controller/recomposition and feature-policy tests are covered by the second
receipt below. The interim receipt is retained as history, not current-source proof.
The baseline's 16 controlled reproductions are unchanged and are **not** a green
regression suite for this implementation.

[Second desktop receipt](evidence/PERM-desktop-second.json), run beginning
**2026-10-24 19:13:34 UTC**: all **72 permission desktop test executions** passed,
with **zero failures, errors or skipped test cases** in the 15 inspected XML reports.

| Desktop scope | Executions passed | XML reports |
|---|---:|---:|
| Core common gate/batch/controller/Compose-runtime tests | 24 | 3 |
| All ten feature modules' common policy/request-owner tests | 48 | 12 |
| Total permissions scope | 72 | 15 |

The [actual command receipt](evidence/gradle/second-library-desktop.log.result.json)
records **overall exit 1**: unrelated UI/navigation test failures and geo/icons
test-compilation failures prevented a successful combined build. The
[root summary](evidence/gradle/second-library-desktop.summary.json) records unchanged
hashes for all 274 selected inputs during that diagnostic. Independent permission
review matched all 75 permission input hashes and all 15 archived XML hashes;
all 139 held permission Kotlin files also still matched the earlier checkpoint.
This is an uncommitted diagnostic snapshot, not immutable release evidence. It
predates the Android test-runner repair below; the fresh core-only desktop/host
execution after that repair is recorded separately below.

That desktop run did not execute the then-existing 12 Android-host-specific tests, Android
ActivityResult/device behavior, JS/Wasm browser tests, or Apple compilation/native
privacy dialogs. In particular, injected native/timer adapters test the production
common request owners, **not** real Bluetooth/local-network prompts or native object
lifetimes. Android-host verification is a separate lead-coordinated gate. This
desktop result alone did not verify or close any finding.

[First Android-host receipt](evidence/PERM-android-host-first.json), run beginning
**2026-10-24 19:17:00 UTC**: the core task **failed** with **36 executions: 33 passed,
three failed, zero errors/skips**, in four inspected XML reports. All 12 Android
registry/planner/runner tests and 21 common gate/batch/controller tests passed. The
three common Compose callback tests failed with `android.os.Trace.beginSection`
not mocked under plain host JUnit; their Unsupported helpers were not Android
permission-factory tests. The
[actual host command](evidence/gradle/first-android-host.log.result.json) exited **1**;
the [root host summary](evidence/gradle/first-android-host.summary.json) records all
173 selected input hashes unchanged during the run. The permission source inputs
were also independently matched before the authorized repair.

The test-runner repair moves the three unchanged scenario bodies into a shared
fixture with non-Android and Robolectric Android wrappers, and adds test-only
Robolectric/JUnit dependencies through the build owner. No blanket Android default
values, skipped tests, or removed assertions are used.
[Fixture integrity evidence](evidence/PERM-host-fixture-integrity.json) reconstructs
the original source SHA-256 exactly after reversing only the declaration/comment/
annotation move. The five new Android factory tests are separate from these common
Unsupported-helper scenarios. They use real AndroidX registrations and result
parsing with injected result intents, a real `LifecycleRegistry`, and Robolectric
permission observations—not an emulator/device or actual process recreation.
Their successful rerun is recorded below; it does not verify OS permission prompts.

### Latest core desktop and Android-host verification

[Core desktop/host receipt](evidence/PERM-core-desktop-android-second.json), run
beginning **2026-10-24 19:33:25 UTC**: both permission core tasks succeeded with
**65 executions: 24 desktop and 41 Android-host**, **zero failures/errors/skips**,
in **eight fresh, independently inspected XML reports**.

| Scope in this run | Passing executions | XML reports |
|---|---:|---:|
| Core desktop common/Compose-runtime tests | 24 | 3 |
| Android-host common controller and request-gate tests | 21 | 2 |
| Android-host shared Compose scenarios with Robolectric runner | 3 | 1 |
| Android-host registry/planner/runner tests with explicit SDK/grant inputs | 12 | 1 |
| Android factory/ActivityResult/lifecycle tests under Robolectric | 5 | 1 |

This resolves the earlier three plain-JUnit setup failures without changing their
shared assertions. The five distinct Android factory cases also passed, including
callback replacement, alias/empty batches, resume-time revocation, disposal and
replacement of a permission while its previous request was pending. Injected
registry result intents and Robolectric grants are **not system-dialog, emulator,
process-kill or device verification**.

The [actual combined command](evidence/gradle/second-io-perm-and-fourth-ui.log.result.json)
still exited **1** because `:calf-file-picker:compileAndroidHostTest` failed in its
unrelated state-restoration test setup. The
[root summary](evidence/gradle/second-io-perm-and-fourth-ui.summary.json) records
260 executed cases passing overall, but a failed compilation means the combined
build did **not** succeed. All 283 selected input hashes were unchanged during the
run; independent area review matched its 30 permission inputs, all eight archived
XML hashes, and all 142 permission Kotlin files against the held post-fixture
checkpoint. The ten feature modules were not rerun in this command; their earlier
48 passing desktop cases remain a separate dated receipt.

All 18 resolution records are now **partially-verified**, limited to their stated
executed scope: common policy/controller tests, the Android-host cases above, or
documentation validation for PERM-024. Apple native adapters, actual Android OS
privacy/version/process behavior, browser targets, binary compatibility and an
immutable release revision remain required gates. No issues are closed. Browser
checks and the iOS KLIB-only diagnostic below remain separately scoped; a KLIB-only
check does not establish Apple linking/device behavior.

### First iOS simulator-arm64 KLIB-only check

[First iOS KLIB receipt](evidence/PERM-ios-klib-first.json), run beginning
**2026-10-24 19:40:54 UTC**, records Linux Kotlin/Native source/typechecking only:

- Core plus eight feature modules—background-location, calendar, camera, contacts,
  gallery, location, microphone and notifications—completed both production and
  test KLIB compilation: **18 compilation tasks across nine modules**.
- Bluetooth and Wi-Fi production compilation failed with **“Mixing Kotlin and
  Objective-C supertypes is not supported”** at then-current helper lines 69 and
  65. Their test KLIB tasks did not execute. The newly introduced probe adapters
  incorrectly combined `NSObject`/native protocol and Kotlin probe interfaces;
  this failure is against the captured implementation hashes, not an upstream
  baseline finding.
- **Zero tests executed.** No Apple link, executable, simulator, device, native
  privacy UI or XCTest ran. This checks `iosSimulatorArm64` declarations/types,
  not runtime behavior or all supported Apple targets.

The [actual command](evidence/gradle/first-ios-klib.log.result.json) exited **1**,
also containing unrelated navigation compile failures. The
[root verification](evidence/gradle/first-ios-klib.verification.json) records all
222 selected input hashes unchanged; independent area review matched all 92
permission inputs before the focused fix.

The two adapters now use composition: a plain Kotlin probe strongly owns a
separate `NSObject`/Objective-C-protocol delegate. Disposal clears its forwarding
closure before detaching/stopping the native object. Bluetooth still handles
synchronous completion during manager construction. The common request owners,
timers, Main-dispatch bridge and all test bodies are unchanged. All four permission
Objective-C delegate declarations were checked; foreground/background location
already used separate native-only protocol objects.
[The refrozen adapter checkpoint](evidence/PERM-ios-adapter-checkpoint.json)
records the exact two changed files and all 142 permission Kotlin hashes.
The [second KLIB receipt](evidence/PERM-ios-klib-second.json), beginning
**2026-10-24 19:50:08 UTC**, confirms that the corrected Bluetooth and Wi-Fi
production and test KLIBs compiled: **four executed compilation tasks, zero test
executions**. All 263 selected input hashes stayed unchanged; area review matched
50 permission inputs and the 142-file source hold. The combined command still
exited **1** from an unrelated UI designated-initializer error. Core was only
UP-TO-DATE in this retry; the other feature modules were not rerun.

Across these separately dated receipts, all eleven permission modules now have
production/test `iosSimulatorArm64` KLIB compilation evidence. **No native tests,
Apple linking or device/privacy UI ran.** Native ownership, prompt behavior and
minimum-OS checks still require Apple runtime/device verification.

Read-only Kotlin2.4.20 platform-klib metadata inspection confirmed the selected
EventKit/Photos/Contacts/CLLocation/CBCentralManager APIs and enum shapes, catching
a CLAccuracyAuthorization qualification issue before a native build. Metadata
inspection is **not** Apple compilation, linking, simulation or device execution.

See the machine-readable [18-record resolution ledger](resolutions/PERM-permissions.json)
for per-finding commands, evidence and remaining limitations. Device/lifecycle,
privacy prompts, native ABI and minimum-OS support are not marked verified merely
because a common policy test passes.

[Checkpoint documentation/schema receipt](evidence/PERM-checkpoint-command.json)
preserves the earlier exact read-only validation: 28 XML snippets parsed, 18 owned
resolution records/paths checked, 84 then-current test functions inventoried and
source hashes stored. The
[post-fixture checkpoint](evidence/PERM-checkpoint-after-host-fixture-command.json)
validates the current 92 declarations/89 distinct scenarios and unchanged shared
test bodies. The
[latest scoped-evidence checkpoint](evidence/PERM-checkpoint-after-green-host-command.json)
also validates the partially-verified ledger and archived test receipts. These are
documentation/source checks, not additional library test executions. The
[post-iOS-adapter checkpoint](evidence/PERM-checkpoint-after-ios-adapter-command.json)
adds the first KLIB-only receipt and current two-file source correction without
counting compilation tasks as tests.


## Current-source JS browser execution — 23:00–23:10 UTC

**Scoped permission result: 72/72 cases passed in 15 fresh XML reports across
11 feature/core modules. The full requested library command failed.** Its
[archived command/results](evidence/js-full-001/receipt.json) began
2026-10-24 at 23:00:48.233382Z, ran 580.12 seconds and exited **1**. Across the
full run, the [archive](evidence/js-full-001/archive.json) records 267 cases:
265 passes and two failures (navigation and WebView). Share test compilation
failed before any share case ran. Those failures are preserved; this permission
result is not an overall JS or repository pass.

| Permission module | Executed cases | XML reports |
|---|---:|---:|
| core | 24 | 3 |
| background-location | 4 | 1 |
| bluetooth | 9 | 2 |
| calendar | 5 | 1 |
| camera | 2 | 1 |
| contacts | 4 | 1 |
| gallery | 4 | 1 |
| location | 4 | 1 |
| microphone | 2 | 1 |
| notifications | 5 | 1 |
| wifi | 9 | 2 |
| **Total** | **72** | **15** |

Every scoped testcase passed without failures, errors or skips. The reviewer
independently matched all 15 sanitized XML hashes to the archive, their original
report hashes to the producer receipt, each testcase name/status to the receipt
and each method name to its held source. Each module has a fresh test-task marker;
report timestamps fall within the recorded run. The permission aggregator itself
has no inherited JS tests and was **not** counted as another successful suite.
The same 72 scenarios have earlier Desktop executions; these are additional
**target executions**, not 72 newly authored tests or an increase from the
89 distinct scenarios/92 annotated declarations documented above.

The runtime receipt identifies **Google Chrome 153.0.8010.36**, Linux x64 and
JDK17.0.20; XML uses ChromeHeadless153.0.0.0. This was real JS browser execution,
not compilation-only, Node or Wasm. The local root-container launcher explicitly
uses `--no-sandbox` and `--disable-dev-shm-usage`. That diagnostic environment is
not a production permission/WebView policy change or browser security clearance.

What these tests actually exercise:

- Core: production request gates, serial batch/full-map behavior, callback-state
  ownership and stale-observation handling, plus three actual Compose-runtime
  callback/recomposition cases. The latter call the internal production
  `rememberUnsupported*` helpers using a no-node composition; they do **not**
  mount the public JS expect/actual factories or render DOM/UI. The trivial JS
  factory delegation compiled, but direct public-factory composition wiring
  remains a distinct integration check.
- Feature modules: common authorization/request policies. Bluetooth and local
  network include injected manager/service/timer request-owner tests; Chrome
  did not acquire Bluetooth hardware, present Apple privacy UI, run Bonjour,
  register with APNs, or exercise EventKit/Photos/Contacts/CoreLocation adapters.
- Unsupported outcomes are explicit contract checks, not browser feature parity.
  No browser camera/location/notification permission service was implemented by
  this run. PERM-024's Android storage/documentation policy has no new
  finding-specific runtime verification here.

The helper's **691-input** before/after snapshots are identical. Its digest is
computed from sorted `hash  path` lines, separately from the archived JSON byte
hash. The archive also records an unchanged broader **703-input** freeze, which
adds 12 notice/identity/license inputs; these counts are different scopes, not
missing library files. Independent area readback matched all **155 captured
permission inputs**, including all 142 permission Kotlin files, to current bytes.
That hash hold includes other-platform sources; it is not evidence that those
platforms executed. The combined scoped
[PERM/GEO JS verification receipt](evidence/PERM-GEO-js-first.json) records all
source/report bindings and the already-existing GEO execution addendum retained.

This addendum supersedes only prior *JS execution pending* statements for the
scoped common/unsupported/helper cases. **Wasm, real Android/Apple native/device
behavior, OS permission/version/process matrices, native/browser service
backends, complete API/ABI/consumer and immutable release gates remain.** All
18 permission resolution statuses stay **partially-verified**; no issues were
closed, source/build files changed or tests launched by this documentation
reviewer. Historical failed diagnostics and KLIB-only limits remain unchanged.


## Latest paired Wasm/JS004 verification — 2026-10-25

**Permission scope: 72/72 cases passed on each target. Both complete-requested
library commands also passed: 290/290 cases in 48 XML reports across 19
test-bearing modules, per target.** These are source-bound local diagnostics,
not immutable release/CI results or proof that every platform feature works.

| Run and exact command receipt | UTC interval | Duration / exit | Permission result |
|---|---|---|---|
| [Wasm004](evidence/wasm-full-004/receipt.json) | 01:25:19–01:27:22 | 123.02 s / 0 | 72/72; 15 XML |
| [JS004](evidence/js-full-004/receipt.json) | 01:28:05–01:30:15 | 130.03 s / 0 | 72/72; 15 XML |

| Permission module | Wasm004 cases | JS004 cases | XML per target |
|---|---:|---:|---:|
| core | 24 | 24 | 3 |
| background-location | 4 | 4 | 1 |
| bluetooth | 9 | 9 | 2 |
| calendar | 5 | 5 | 1 |
| camera | 2 | 2 | 1 |
| contacts | 4 | 4 | 1 |
| gallery | 4 | 4 | 1 |
| location | 4 | 4 | 1 |
| microphone | 2 | 2 | 1 |
| notifications | 5 | 5 | 1 |
| wifi | 9 | 9 | 2 |
| **Total** | **72** | **72** | **15** |

There were no failures, errors or skips in these cases. The permission aggregator
still has no inherited browser tests and is not counted as a passing suite. The
same 72 source methods ran on both targets: **144 target executions, not 144
distinct tests**. This does not increase the earlier permission inventory of
89 distinct scenarios / 92 annotated declarations.

The independent [paired PERM/GEO readback](evidence/PERM-GEO-browser-004.json)
checked all 58 archive checksum entries and 24 context checksum entries per run,
reconstructed all 48 sanitized XML reports from the available original reports,
matched raw/archived/producer hashes and testcase outcomes, and checked fresh
task markers and report/configuration timestamps. All 72 permission cases per
target map to the held annotated source methods. This integrity recount covers
the full run; implementation-level interpretation here remains permission/geo
scope, not a new semantic review of the other modules.

Both runs used the **same 693 selected inputs**, unchanged before/after each run
and at this readback. All **155 permission inputs, including every one of the
142 permission Kotlin files**, match. The input content digest (sorted
`hash  path` lines) is not the snapshot JSON byte hash. The historical 703-input
Yarn-bootstrap snapshot is a different, earlier scope; these archives explicitly
list subsequent drift rather than claiming that old freeze still holds.

The [Wasm context](evidence/wasm-full-004-context/context-review.json) is bound to
fresh generated Karma configurations using the requested prepared Kotlin tooling
home; [JS context](evidence/js-full-004-context/context-review.json) instead uses
`build/js`. All 19 configuration bindings per target were rechecked. Only the
first literal `config.set` selection is covered: later executable configuration,
the full installed dependency graph, ordinary frozen-lock enforcement and
independent dependency provenance are **not** certified. Runtime receipts name
Chrome **153.0.8010.36**, Linux x64 and JDK **17.0.20**. The existing root-container
wrapper uses `--no-sandbox --disable-dev-shm-usage`; this remains a disclosed
diagnostic limitation, not a production security-policy change.

Coverage remains precise:

- Core's 24 cases comprise eight callback-state, 13 request-gate/batch and three
  Compose-runtime callback/recomposition cases. The three Compose cases call
  internal production `rememberUnsupported*` helpers with a no-node applier.
  The public permission factory → internal expect/actual → helper wiring
  **compiled but was not mounted by these tests**, on either browser target.
- Feature policies and Bluetooth/local-network request owners use injected
  provider/timer events. No Android permission/ActivityResult implementation,
  Apple framework/privacy UI, Bluetooth hardware, Bonjour or APNs ran in Chrome.
  These tests do not establish minimum-OS, process-death, native callback-queue
  or physical-device ownership behavior.
- Unsupported contracts are not implemented browser permission services.
  Camera/location/notification browser service backends and desktop native
  backends remain separate work. **PERM-024 has zero new finding-specific
  storage-policy runtime coverage** from either run.

This latest addendum supersedes the earlier dated *Wasm execution pending*
statements only for the listed common/helper cases. All 18 permission findings
remain **partially-verified**. Direct public-factory composition, native/device/
privacy matrices, ABI/Maven consumers and an immutable release candidate remain
gates. The earlier [JS001 failures](evidence/js-full-001/archive.json), including
navigation/WebView and share test compilation, and failed/incomplete
[Wasm001](evidence/wasm-full-001/archive.json),
[Wasm002](evidence/wasm-full-002/archive.json) and
[Wasm003](evidence/wasm-full-003/archive.json) are preserved, not rewritten by
these later passes. No source/test/build/script edits, new test launches,
GitHub mutations, commits or publication occurred in this documentation handoff.
