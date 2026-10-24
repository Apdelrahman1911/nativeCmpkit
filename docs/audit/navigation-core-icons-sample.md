# Technical audit: navigation, core, icon assets and sample applications

**Baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`.
**Review date:** 2026-10-24. **Environment:** Linux; no Apple/device behavior is
certified. All source locations in [NAV.json](findings/NAV.json) refer to the
baseline, even when migration changes current line numbers or notices.

The [module report](../modules/navigation-core-icons-sample.md) documents the
execution flows, every important function/API family and all platform shells.
The [test report](../testing/navigation-core-icons-sample.md) distinguishes executed
checks, source proofs and required device/build work. This report explains the
technical conclusions and their limits; JSON findings are the issue-generation
source of truth.

## Executive assessment

- **Core is deliberately small.** All nine files were read; its context and opt-in
  boundaries are internally understandable. No standalone correctness defect was
  confirmed in core. This is source review, not a successful core build or proof
  that host apps always supply a suitable Android Context.
- **Navigation is a prototype, not production-ready navigation.** Its public
  argument parameter is ignored, repeated routes alias saved state, and multiple
  contract/helper bugs were reproduced from unchanged baseline Kotlin source.
  It lacks a publication plugin and was advertised as coming soon. Preserve that
  boundary until the API/lifecycle decision and regression tests are complete.
- **The Cupertino catalogue/font are structurally coherent.** All 1,322 constants
  exist in the font and sample; all 6,984 SF-name declarations parse uniquely.
  This does not prove rendering, glyph identity, Apple availability or accessible
  speech. A known missing font MIT notice is repaired in the migration source
  tree, with artifact notice verification still required.
- **The sample exercises a broad API surface but is not a test suite.** Secure
  text is logged, the export pipeline is unbounded/error-unhandled, the byte-count
  loop is not cancellation-cooperative, permission menu/manifest declarations
  disagree, and one illustrative share button reports a copy it never made.
  Many other sample buttons intentionally demonstrate appearance only.
- **No local full Gradle navigation test suite completed.** The centrally owned
  build attempt was stopped on resource constraints before test execution. Ten
  isolated JVM baseline-behavior assertions passed; several deliberately assert
  the presence of defects. Never summarize that as ten passing product tests.

## Findings register and triage

There are **18 NAV findings: 3 High, 13 Medium, 2 Low**. Status distribution:
10 confirmed-source, 4 confirmed-test, 3 improvement, 1 risk. These statuses are
evidence types, not completion state; source-tree notice remediation is explicitly
called out in `NAV-009`/`NAV-018` rather than silently deleting baseline evidence.

| ID | Priority / evidence | Principal issue and boundary |
|---|---|---|
| NAV-001 | High / confirmed-source | `navigate` arguments discarded; content receives graph schema, not entry values |
| NAV-002 | High / confirmed-source | Route rather than entry identity keys saved state; incomplete duplicate-entry handling after #542 |
| NAV-003 | Medium / confirmed-test | Required typed/null-default arguments rejected; wrong-type defaults accepted until a later cast |
| NAV-004 | Medium / confirmed-test | Erased bundle getter, string coercion and incomplete generic insertion violate contracts |
| NAV-005 | Medium / confirmed-test | Missing StringArray inference, unescaped/null-ambiguous serialization; inactive custom type branches |
| NAV-006 | Medium / confirmed-source | Keyless graph/effect capture stale controller, builder and callbacks |
| NAV-007 | Medium / confirmed-source | Unknown or duplicate routes silently produce empty/first-match content |
| NAV-008 | Medium / improvement | Decide controller architecture and document absent platform navigation capabilities before release |
| NAV-009 | High / confirmed-test | Proven Cupertino MIT asset needs notices in artifacts; migration repairs source notice gap |
| NAV-010 | Medium / confirmed-source | Glyph Text semantics remain under decorative/labeled icon wrapper |
| NAV-011 | Medium / improvement | No reconstructible catalogue generator/version mapping/Apple availability metadata |
| NAV-012 | Medium / confirmed-source | Secure sample password field prints the entered value |
| NAV-013 | Medium / confirmed-source | Sample image export reads/allocates unbounded data, allows overlap and lacks error handling |
| NAV-014 | Medium / confirmed-source | Cancelled streaming sample can keep reading until EOF |
| NAV-015 | Medium / confirmed-source | Android Call demo lacks declaration; unrelated broad permissions confuse least-privilege example |
| NAV-016 | Low / improvement | Unused second navigation dependency adds compatibility footprint |
| NAV-017 | Low / confirmed-source | Showcase's clipboard success message has no corresponding operation |
| NAV-018 | Medium / risk | Reconstruct derived Apache-source attribution and verify distribution notices |

`NAV.json` provides exact paths/lines/symbols, root causes, consequences, fixes,
change risks, regression tests, immutable evidence, upstream references, effort
and dependencies for every row. None of these issues authorizes a rewrite,
release or package publication during the migration.

## Navigation correctness: source proofs and reproducible cases

### 1. Argument values have no path through the implementation

Controller storage is `MutableList<String>` (`AdaptiveNavHostController.kt:16`).
The method accepts a `Map<String, NavArgument>` but only appends a route at24.
Destination definitions independently hold another map. Host dispatch at
`AdaptiveNavHost.kt:43` passes **that definition map** directly to content.
There is no merge, argument bundle, per-visit payload, validation or restore
mechanism in between. A wrong or missing runtime argument cannot be detected
because the input is discarded before content is selected. This is established
by the full data flow; a device is not necessary to establish unused input.

The fix must not simply append another parallel map indexed by route. That would
repeat the duplicate-entry identity defect. Define entry identity, resolved
values and restoration together, with a migration policy for the current
String-array saver. A type-safe route architecture is a later design choice,
not a migration prerequisite.

### 2. The #542 state fix works only for distinct route names

Baseline code has a route-keyed `SaveableStateProvider` and removes state for
route names absent from the current stack's set. Trace these cases:

| Sequence | Source consequence |
|---|---|
| Home(counter1) -> Detail -> pop | Home remains as a route; its saved state is available. Existing test covers this |
| Home -> Detail(counter1) -> pop -> idle -> Detail | Detail disappeared between compositions; saved state is removed. Existing test covers this |
| A(counter1) -> B -> A | The second A uses the first A's key and saved state instead of a fresh entry |
| A(counter1) -> A | Same current route/key/composition position; no entry change distinguishes the new visit |
| A -> B -> A -> pop A while an earlier A remains | Set still contains A; cleanup cannot delete only the popped visit's state |
| Pop Detail and re-push Detail before an observed composition | Before/after route sets contain Detail; cleanup has no evidence an entry ended |

These are deductions from the explicit key algorithm, not claims that a Compose
test was run for these scenarios. Add a unique stable entry ID and tests for both
plain `remember` and `rememberSaveable` semantics. Ensure all popped entry state is
removed without evicting another live instance. Do not assume a route is the same
as an AndroidX back-stack entry owner.

### 3. Builder/type/bundle failures are executable without Compose

The independent runner extracts exactly `AdaptiveBaseBundle.kt`,
`AdaptiveBundle.kt`, `AdaptiveNavType.kt`, `NavArgument.kt` from the baseline and
compiles them unchanged with cached Kotlin2.4.20. No stubs or replacement parsing
implementation are used. Its observed cases include:

```kotlin
// Unexpectedly rejects despite an explicitly declared type:
NavArgument.Builder().setType(AdaptiveNavType.IntType).build()

// Unexpectedly rejects an explicitly allowed null default:
NavArgument.Builder().setType(AdaptiveNavType.StringType)
    .setIsNullable(true).setDefaultValue(null).build()

// Builds, then throws ClassCastException when putting the default:
val bad = NavArgument.Builder().setType(AdaptiveNavType.IntType)
    .setDefaultValue("not-an-int").build()
bad.putDefaultValue("n", AdaptiveBundle())
```

The same runner proves that inferred StringArray throws despite explicit
StringArrayType working; a generic String lookup of a stored Int throws on JVM;
`getString` of Int42 yields `"42"` rather than fallback; `putObject(1.5f)` rejects
despite `putFloat` working; URI-delimiter strings are returned unescaped.
Positive controls confirm strict Boolean rejection, hexadecimal Int/Long parsing,
uppercase Long suffix, append order and `NavArgument.verify` behavior.

The source also shows array `toString` serialization is not a codec, string null
and literal `"null"` collide, and repeated primitive-array `plus` copies are
quadratic in total appended values. These additional source observations were
not misrepresented as measured benchmarks. No working host deep-link parser
exists, so there is **no confirmed deep-link injection vulnerability** in these
helpers. JVM erased-cast evidence must be ported to JS/Wasm/Native tests before
assuming identical platform failure modes.

### 4. Composition lifetime and graph validity need an explicit contract

`remember { builder() }` captures the initial graph; `LaunchedEffect(Unit)` only
initializes the initial controller. Passing a new empty controller can leave the
host empty while old graph lambdas retain old callbacks. Simply adding every
lambda as a remember key can cause constant graph rebuilding. Prefer stable graph
specifications plus intentional callback updates and controller-lifetime keys.
Route validation must cover initial, navigate and restored routes. Different
behavior may be appropriate for debugging versus production, but a silent blank
Box is not an actionable diagnostic.

## Font, accessibility and attribution evidence

### What was actually verified

The baseline TTF is **exactly** the Flutter CupertinoIcons Version1.08 font at
`flutter/packages@23a05b6ad5d55bc0df5b9340623570b69064edf1`,
`third_party/packages/cupertino_icons/assets/CupertinoIcons.ttf`. SHA256:
`67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c`.
The accompanying MIT file contains Copyright(c)2016 Vladimir Kharlampidi and is
preserved verbatim in `licenses/cupertino-icons-MIT.txt`. Source history/metadata
support import through #511. The obsolete `nicklama/cupertino_icons` link is not
necessary for the new repository's retained local notice/evidence.

The offline checker parses all generated identifiers including backtick-escaped
`repeat`, `case` and `return`; it fails if a declaration is skipped. It verifies
uniqueness, catalogue correspondence, BMP range and nonzero Unicode cmap glyph
coverage. **Aliases are valid**: 1,322 names map to1,234 codepoints; this is not a
duplicate-constant error. Likewise a larger total font cmap than exposed
constants does not prove missing public APIs are defects.

### What remains unverified

- The correct visual glyph for each human-readable name, baseline alignment,
  antialiasing, scaling, high contrast, first-load behavior and actual platform
  resource packaging.
- VoiceOver/TalkBack/desktop/browser speech. The source clearly leaves a Text
  semantics node containing a private-use character, but its exact utterance
  depends on assistive technology and composition merging.
- Apple symbol availability on the oldest supported deployment target. The SF
  catalogue is a list of names, not the Apple font. `UIImage.systemImageNamed`
  returns a nullable image; missing images are not automatically a crash.
- Inclusion of local notices in AAR/JAR/KLIB/native/web/sample distributions.
  Adding `licenses/` to Git alone is not evidence that release archives carry it.

### Other copied-source attribution

The notice extension records verified Apache2 reference evidence for
Compose Cupertino's slider and Kyant's AndroidLiquidGlass samples/utilities;
the UI reviewer traced the executable changes. The reference commits are
**observation pins, not proven original copy revisions**. The baseline code
credits both projects in comments but does not preserve all source copyright
headers. One package-stripped drag utility matches the pinned Kyant source
exactly; related utilities are close adaptations.

Navigation's NavArgument/NavType and Bundle descriptions contain extensive
AndroidX/AOSP material. Pinned reference headers identify AOSP copyright2018 for
NavArgument/NavType,2014 for BaseBundle,2007 for Bundle. Android-only lazy/parcel
comments retained in the common adaptation are additional provenance signals.
The exact originally copied revisions remain unestablished; `NAV-018` is a
compliance/provenance **risk**, not a legal certification or a finding that a
current external commit was necessarily the source used at import time.

Jodd's existing five complete identical BSD2 headers **were present** at baseline,
not missing. A consolidated local license copy was added for convenience and
binary-notice planning, without inventing another missing-license finding. See
`THIRD_PARTY_NOTICES.md` and machine-readable files in `licenses/`.

## Sample correctness, resource use and security boundaries

| Concern | Confirmed facts | Risk / required validation |
|---|---|---|
| Sensitive output | AlertDialogScreen264 prints secure-field input on every callback | Local logs can expose entered values; no evidence of network exfiltration. Use synthetic strings for regression capture |
| Export dispatch | FileSaverScreen173 calls whole-file read before its Default block; Android/JVM/iOS actuals perform blocking operations despite suspend signatures | UI stalls depend on device/input. Move I/O appropriately; a browser Default dispatcher is not a native worker guarantee |
| Export memory/errors | Whole input bytes, full decoded image, cropped bitmap and PNG coexist; multiple clicks launch overlapping jobs; no catch/busy state | Peak memory/OOM threshold and native Skia lifetime need profiling; no measured leak is claimed. Encoder Boolean/null handling requires tests |
| Image list | Every selected file becomes an AsyncImage in a scrolling Column | Large multi-selection can trigger unnecessary composition/load work; use bounded lazy rendering rather than assuming typical tiny selections |
| Streaming | Source is in `use`; cancellation is rethrown; count loop has no check/suspension | Cancellation cannot stop synchronous loop until EOF/failure. Underlying reads may still be uninterruptible. Browser source buffering is a separate IO limitation |
| Manifest | Call requested but CALL_PHONE absent; MANAGE_EXTERNAL_STORAGE and SMS permissions declared without matching active demos | Merged manifest/device/API-level behavior must be tested; declaration is not a grant or proof of broad file access |
| False success | Showcase's callbacks only set a Boolean before saying a link was copied | Misleading demo assertion, not proof the actual ShareScreen launcher is broken |
| Tab/local state | Large demo tabs use AnimatedContent and plain remember without per-tab retention | Reset may be acceptable demo behavior; document/test rather than automatically treating every reset as a library defect |

The sample FileProvider is nonexported, permits URI grants, and is scoped to cache
paths. A `.` cache-path entry alone does **not** mean any app can read all storage.
The exact URIs/actions granted by camera/share are audited in native-feature code.
Likewise `INTERNET` or JavaScript enabled in a demonstration is not automatically a
confirmed vulnerability: embedded WebView trust/callback issues are examined by
the responsible native reviewer.

`MapScreen` and the entirely commented expandable-FAB/Second.ios examples are
retained source history, not shipped feature implementations. Xcode's project-
level26 target is overridden by app target18.5 at baseline314/361. iOS26 SDK needs,
iOS deployment minimums, local version gating and future API availability are four
different facts; none can substitute for a successful Xcode/device run.

## Historical review and incomplete fixes

Public archived metadata is evidence, not instructions. The relevant source
changes and archived PR/issue bodies/comments were reviewed against baseline:

| Upstream reference | What history establishes; limits |
|---|---|
| [#542](https://github.com/MohamedRejeb/Calf/pull/542), commit `1554f1b7758e634faf93cd4e851046b94b3fb954` | Merged state-retention fix adds route-key holder, route-set cleanup and two desktop tests. Fixes two distinct-route cases, not entry identity. No reviewed discussion resolves duplicate-route behavior |
| [#510](https://github.com/MohamedRejeb/Calf/pull/510), `815d076640acae73480d507eee91421f6a7228f9` | Adds SF symbol string catalogue; no reproducible generator identified |
| [#511](https://github.com/MohamedRejeb/Calf/pull/511), `65e8433222f2731c0d0e4c3849dc0cd937bc8b46` | Introduces bundled Cupertino font/module, moves SF name constants into UI; baseline source archive lacked font MIT notice |
| [#514](https://github.com/MohamedRejeb/Calf/pull/514) | Icon package adjustment leads to current `com.mohamedrejeb.calf.cupertino.icons`; retain this namespace for compatibility |
| [#545](https://github.com/MohamedRejeb/Calf/pull/545), closes [#537](https://github.com/MohamedRejeb/Calf/issues/537) | Streaming API/sample added. PR explicitly acknowledges browser full buffering; sample KDoc claiming the whole file never needs to fit in memory is overbroad. Does not establish cooperative cancellation |
| [#546](https://github.com/MohamedRejeb/Calf/pull/546) | Toolchain/SDK compatibility decisions explain Android navigation2.9.7 versus sample JetBrains2.10-alpha and minSdk23/24. Past claims of green builds/releases are not independent results of this audit |
| [#139](https://github.com/MohamedRejeb/Calf/issues/139) | Older Compose/navigation version-mismatch discussion demonstrates integration sensitivity. It is not evidence that the current Adaptive duplicate-route bug is the same issue |
| [#551](https://github.com/MohamedRejeb/Calf/pull/551) | Open/unmerged picker/export/bookmark overhaul at archive time. Not in baseline; proposed fixes/emulator claims must not be reported as already implemented or independently verified |

Metadata lives under `docs/migration/upstream-metadata/` (issues, PRs, issue/review
comments and per-PR GraphQL records) and full imported Git objects preserve code
history. Link findings to these originals rather than reopening duplicates without
explaining the remaining defect. Migration does not modify upstream.

## Coverage, positive checks and limitations

### Positive checks

- Every handwritten assigned Kotlin/Swift file and all Gradle/manifest/plist/Xcode/
  XML/HTML/asset metadata were read; large942-line NavigationBar and788-line
  Showcase implementations and commented prototypes were not skipped.
- Core platform aliases/locals match their intended Android versus sentinel role.
- Controller pop protects a sole root when called through its method; typed
  primitive bundle getters generally honor fallback behavior; Boolean parsing
  does not silently accept arbitrary strings.
- Stream demo uses `use` and does not swallow CancellationException; desktop app
  provides its Window to file picker integration.
- Both original navigation tests were inspected, with their limited distinct-route
  scenarios documented rather than discounted or claimed to cover all stacks.
- All generated declarations, catalogue references and codepoint coverage were
  checked; MIT font provenance is based on bytes, not a filename assumption.

### Unavailable or incomplete checks

- No iOS build, UIKit render, interactive gesture, memory graph, native font
  accessibility, privacy prompt or app-signing test from this Linux reviewer.
- No Android device/emulator lifecycle/back/permission test, desktop GUI runtime,
  browser history/keyboard test, full web sample run, or real assistive-technology
  session attributable to these local checks.
- No performance profile, allocation benchmark, fuzz test, API binary-compatibility
  baseline or artifact-distribution legal certification.
- No original exact upstream revision reconstructed for all copied Apache source;
  reference pins and local notices reduce dependency on live remote pages but are
  not a complete third-party provenance/SBOM audit.
- Full Gradle suite was blocked/stopped before tests, not observed failing on a
  navigation Kotlin/Compose assertion. Later remotely verified results, if any,
  belong in the central ledger with commit/run/test counts.

## Recommended implementation order

1. **Immediate safe demo/notice work:** remove secure-value logging, make demo
   success messages truthful, retain/license assets and derived-code notices;
   verify packaging before any later publishing authorization.
2. **Navigation design gate:** decide mature-library adapter versus deliberately
   small independent stack (`NAV-008`); define entry/payload/lifecycle/saver rules.
3. **Navigation correctness:** implement values/entry identity (`NAV-001/002`),
   construction/access/codec contracts (`NAV-003/004/005`), then controller graph
   lifetime and registration validation (`NAV-006/007`) with cross-target tests.
4. **Demo reliability and accessibility:** cooperative bounded I/O, manifest
   scenarios and icon semantics; validate on devices and adversarial inputs.
5. **Reproducibility/cleanup:** catalogue generator/availability, remove unused
   dependency, complete performance/resource and binary-compatibility testing.

This is a roadmap dependency order, not authorization to undertake a major
architectural rewrite before audit integration.
