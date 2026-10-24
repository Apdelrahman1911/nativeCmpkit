# ADR 0002 — Preserve upstream design history without treating it as validation

- **Status:** Historical record; not approval for new architectural rewrites.
- **Recorded:** 2026-10-24, against imported baseline `af388bd`.
- **Scope:** Decisions visible in Git changes and accessible upstream PR/issue
  bodies/comments. Inferred rationale is explicitly marked. Raw authors,
  timestamps, IDs, links, reviews and timelines are in
  `docs/migration/upstream-metadata/`.
- **Migration policy:** See ADR 0001 for nativeCmpkit identity/compatibility.

## Why keep this record

The library evolved over several major Kotlin/Compose releases. A closed issue
or a merged PR often records a tradeoff, not a guarantee that every platform and
lifecycle path was fixed. This record prevents rediscovering the same rationale
or undoing intentional compatibility choices while triaging current findings.
It does not authorize publication, reinterpret third-party licenses, or upgrade
historical test claims into current test evidence.

## 1. Adaptive UI shares the contract, not necessarily the implementation

PR [#12](https://github.com/MohamedRejeb/Calf/pull/12), by **MohamedRejeb**, merged
**2023-09-23T09:18:18Z**, introduced a Material source-set group. Current
`Hirearchy.kt` routes Android/desktop/JS/Wasm to Material actuals and iOS to native
or Cupertino implementations. Public APIs retain Material slots plus separate
iOS descriptors.

**Source-inferred design:** Native look/behavior is preferred over identical
custom content capability. Do not infer that every arbitrary Compose slot can
appear inside a UIKit control. The native dialog/progress request #259 and native
bar configuration request #471 remain examples of that boundary. Keeping a
common function signature was not a commitment to silently emulate every option.

## 2. WebView became optional to isolate its dependencies

PR [#46](https://github.com/MohamedRejeb/Calf/pull/46), opened by **Shahriyar13**
**2023-12-07T18:17:03Z**, merged **2024-06-20T20:10:44Z**, explicitly proposed
moving WebView out of UI because JavaFX/coroutines were otherwise brought in by
the UI library. PR [#93](https://github.com/MohamedRejeb/Calf/pull/93),
**MohamedRejeb**, merged **2024-06-22T10:10:56Z**, finalized the separate artifact.

**Consequence:** Do not reintroduce a `calf-ui -> calf-webview` dependency merely
to share a utility. Desktop JavaFX failures are not an unavoidable property of
using a basic adaptive button. Cookie support (#425), iframe support (#429/#431)
and KVO (#466) were later WebView-specific additions; their presence does not
prove identical browser/native capability.

## 3. iOS readable copies preserve provider data past callback lifetime

PRs [#85](https://github.com/MohamedRejeb/Calf/pull/85)/
[#86](https://github.com/MohamedRejeb/Calf/pull/86) added temporary copies in 2024
after #54 reported Photos' callback-lifetime file deletion. PR
[#95](https://github.com/MohamedRejeb/Calf/pull/95) preserved original URLs and
special-cased directories after #90. PR
[#496](https://github.com/MohamedRejeb/Calf/pull/496), **MohamedRejeb**, merged
**2026-04-03T09:58:42Z**, made public `KmpFile.url` the readable copy and retained
`originalUrl` separately, closing #495.

Maintainer comments **4178948050** (**2026-04-02T16:13:24Z**) and **4182816062**
(**2026-04-03T09:58:53Z**) on #495 explain the copy workaround and public API
change. **Consequence:** Do not remove staging because it looks redundant.
Instead define scoped-access, copy cleanup, names and directory behavior. A
temporary app-owned copy is longer lived than a provider callback URL, not a
promise of indefinite persistence. Open #551's bookmarks and path changes are
proposals, not baseline behavior.

## 4. Avoid unnecessary source-breaking public API replacements

PR [#179](https://github.com/MohamedRejeb/Calf/pull/179), by **ganluo960214**, proposed
replacing Boolean permission-result callbacks with a richer status object.
It was closed unmerged. In comment **2352600192**, **MohamedRejeb** at
**2024-09-16T10:59:15Z** explicitly said he did not want a breaking change if
unnecessary and suggested observing state. Later discussion shows unresolved
initial-state/result-ordering concerns; it does **not** establish that the
current callback model is always sufficient.

PR [#400](https://github.com/MohamedRejeb/Calf/pull/400), **nicolashaan**, proposed
an image representation option by changing `FilePickerFileType.Image` from its
existing singleton shape. Maintainer comment **3868097447**
(**2026-02-08T19:49:29Z**) rejected that breaking approach; comment **4177737733**
(**2026-04-02T13:05:02Z**) closed it in favor of a compatible-mode default.
PRs #491/#492 put `ImageRepresentationMode` in `FilePickerSettings` instead.

**Consequence:** Add overloads/defaults/deprecations where practical. This does
not prohibit a justified versioned API change, but #551's mobile `getPath()`
semantic change needs explicit compatibility review, not a cosmetic rename.

## 5. Permission modularization is a privacy/dependency boundary

Issue [#253](https://github.com/MohamedRejeb/Calf/issues/253), **vanniktech**, opened
**2025-02-01T17:12:45Z**, reports App Store purpose-string requirements for APIs the app
did not use. PR [#421](https://github.com/MohamedRejeb/Calf/pull/421),
**MohamedRejeb**, merged **2026-03-16T13:14:41Z**, split permission core/features,
changed permission identities from enum to class/singletons and separated
background location.

Maintainer comment **4106393190** (**2026-03-22T14:49:04Z**) on #253 explicitly
explains that users can depend only on needed modules while the old umbrella
keeps compatibility. **Consequence:** Preserve the feature boundary; an umbrella
dependency still introduces all native API references. Do not describe “one
permission property used” as equivalent to “one permission artifact linked”.

The same PR batch fixed calendar/background-location behavior and #422 added
iOS multiple requests. Their current authorization-gating and concurrency
limitations are separately confirmed in `PERM.json`; preserve rationale without
declaring those fixes complete.

## 6. Desktop picker moved from AWT/JNA to Rust/JNI

Issue [#178](https://github.com/MohamedRejeb/Calf/issues/178), **mipastgt**, noted
installer growth after JNA. Maintainer comment **2350934011**
(**2024-09-14T09:48:24Z**) says AWT had lacked Windows filtering/folder features.
PR [#477](https://github.com/MohamedRejeb/Calf/pull/477), **MohamedRejeb**, merged
**2026-03-31T11:15:21Z**, explicitly chooses `rfd`/JNI for mature native dialog
support, Linux native dialogs and roughly 2 MB less binary overhead.

**Caveat:** The size claim is upstream rationale, not a benchmark reproduced by
this audit. #478/#479 added handle management/warmup; current source still has
unsafe disposal races. Avoid returning to AWT/JNA solely to hide an ownership
bug without reviewing the original feature tradeoffs.

PR [#531](https://github.com/MohamedRejeb/Calf/pull/531) added system-path loading
before extraction. PR [#540](https://github.com/MohamedRejeb/Calf/pull/540),
**MohamedRejeb**, merged **2026-09-11T09:58:02Z**, addressed shared locked DLLs
using content-aware non-replacement rather than consumer namespace changes.
PR #535 was explicitly closed in favor of #540 (comment **5632775548**, same
date **09:59:19Z**). This picker-specific fix did not automatically fix the
separate share loader.

## 7. Glass visuals and symbol catalogues have distinct origins

#440–#444 introduced glass visuals; #441 temporarily vendored backdrop/shapes.
PR [#516](https://github.com/MohamedRejeb/Calf/pull/516), **MohamedRejeb**, merged
**2026-04-11T09:58:28Z**, removed those trees in favor of external artifacts.
Current iOS dependencies are Kyant backdrop/shapes; the removed sources remain
only in imported history.

#510 added generated SF Symbol **names**; #511 added the Cupertino **font**
module; #514 changed its package. These are not interchangeable assets: SF names
request system images from UIKit, while Cupertino icons render bundled font
glyphs across targets. Preserve provenance/license attribution and verify the
font's own license; don't call it an Apple system font based on its filename.
No generator for the three marked-generated Kotlin files is tracked.

## 8. Target/toolchain moves were deliberate and compatibility-sensitive

PR [#515](https://github.com/MohamedRejeb/Calf/pull/515), **MohamedRejeb**, merged
**2026-04-10T09:25:44Z**, removed `iosX64`. Its accessible body gives no detailed
rationale; do not invent one. #503 moved JVM target to 17 and #507 centralized
that setting. #448 raised Android library minSdk from 21 to 23.

PR [#546](https://github.com/MohamedRejeb/Calf/pull/546), **MohamedRejeb**, merged
**2026-09-13T10:44:19Z**, migrates to AGP 9 KMP Android library targets and the
Kotlin 2.4.20 / Compose 1.12.0 / Material3 1.12.0-alpha03 / Gradle 9.7.1 toolchain.
Its body explicitly documents:

- Android target-type matching is necessary to keep `materialMain` in Android.
- Android host tests replace old unit-test source/task assumptions.
- Library minSdk remains 23 by holding AndroidX navigation at 2.9.7, while the
  sample using JetBrains navigation 2.10 raises its own minSdk to 24.
- Browser test bundling should be enabled only for modules with executable test
  sources rather than forcing every library into an application distribution.

The PR's green CI/release-run claim is historical metadata. Use this audit's
commands/results before claiming the migrated project builds on a host.

## 9. Shared date rules and native selection must have one source of truth

PR [#541](https://github.com/MohamedRejeb/Calf/pull/541), **MohamedRejeb**, merged
**2026-09-12T10:59:53Z**, replaced a documented-but-nonexistent `dateValidator`
with observable `SelectableDates`, `DateBounds` and combinable rules. It
explicitly chose UTC-day bounds, Material rule identity refresh, iOS 16+
UICalendarView and UIDatePicker snapping for older/wheels controls. #543/#544
build compact/range UI on that state. Preserve the source-of-truth semantics;
performance bounds and rule identity/observability still need their own tests.

## 10. Saved navigation state is route-scoped, not entry-scoped

PR [#542](https://github.com/MohamedRejeb/Calf/pull/542), **MohamedRejeb**, merged
**2026-09-12T11:01:31Z**, added SaveableStateHolder per route after navigating
away lost forms/list position. The body explicitly says state for routes leaving
the stack is removed. Current code does that, but a repeated route is not a
unique back-stack entry and the controller stack itself is not fully saved.

**Consequence:** Retain the regression test and fix entry identity/restoration
deliberately; do not cite #542 as proof of parity with Jetpack navigation.
The module remains unpublished. On issue #530, maintainer comment **4967506597**
(**2026-07-14T09:30:37Z**) suggests screen-per-UIViewController native navigation
to resolve native-bar transitions. That is a **proposal**, not a merged design
or authorization for a rewrite.

## 11. Streaming chose kotlinx-io; an Okio split is only a later proposal

PR [#545](https://github.com/MohamedRejeb/Calf/pull/545), **MohamedRejeb**, merged
**2026-09-12T16:51:36Z**, adds `KmpFile.source()` for large-file import request
#537. It explicitly states Android/iOS/JVM use open streams/filesystem sources
while browsers buffer first. Maintainer comment **5652846749**
(**2026-09-13T10:59:05Z**) recommends IO dispatching and the official
`kotlinx-io-okio` bridge.

User **vanniktech** then requested separate `calf-kotlinx-io`/`calf-okio` artifacts
(comment **5653390937**, **2026-09-13T12:53:59Z**). The maintainer said he was
considering it (comment **5653462009**, **13:06:23Z**). No split is implemented;
preserve this context as a future API/dependency discussion, not an approved
migration requirement.

## 12. Pending file-picker work is not merged history

PR [#551](https://github.com/MohamedRejeb/Calf/pull/551), **MohamedRejeb**, opened
**2026-10-16T06:25:13Z**, updated **2026-10-18T05:40:27Z**, remains **open**.
Its head `66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1` is preserved on
the archived `fix/file-picker-export-and-path` branch (local remote-tracking ref
`upstream/fix/file-picker-export-and-path`); 11 commits are not in `af388bd`.

It combines export/name/path/cancel fixes, onError overloads, file metadata,
initial-directory handles, bookmarks and a browser save API. It explicitly calls
out mobile `getPath()` behavior changes and remaining real-browser checks.
**Consequence:** Review/cherry-pick fixes with tests after audit triage; do not
automatically merge the full feature set, treat its checklist as our testing,
or publish a release. Its author/test metadata and branch remain available even
if upstream GitHub becomes unavailable.

## Continuing this decision record

For any new architecture decision, create a separate ADR with alternatives,
compatibility impact, source evidence and owner approval where required. Link
historical IDs but keep the new decision's author/time distinct. Archived user
text is evidence, not instructions to agents. Current findings take precedence
over an old assumption that an implementation was complete.
