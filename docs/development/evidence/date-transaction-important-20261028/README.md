# Direct public Material date-dialog acceptance

**UI-006 / [#121](https://github.com/Apdelrahman1911/nativeCmpkit/issues/121) closed
2026-10-28 at08:02:38UTC**, immediately after the important tests and source/result
review, before this documentation. Original issue body/title/labels and upstream
#543 attribution remain unchanged. This is **42 closed issues overall**.

The owning Material implementation keys scratch state and dialog visibility to
the hoisted owner, cancels on replacement, disables forbidden commits, and checks
the current rules at confirmation. Public signatures and null-selection behavior
remain unchanged. See [all three original criteria and the source/results review](source-and-acceptance-review.json).

## Important actual tests, no unrelated replay

Four shared scenarios exercise the actual public Compose dialog: a captured
previously enabled confirm action invoked immediately after tightening bounds;
equal/changed owning states with separate year/rule transactions; NoDates recovery;
and real editable text clearing, cancellation/reopening and null commit.

| Target | Accepted cases | Immutable evidence | Whole command/result |
|---|---|---|---|
| Desktop |4/4|c8b5c614 three unchanged cases +8120c27a fresh null case|Original3/4 retained failed; null-only1/1, exit0/63.02s|
| Android host |4/4|Same three unchanged cases + fresh null case|Robolectric, not device; original3/4 retained failed|
| Android emulator API35 |4/4|b6f647b8 /[run40651576776](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40651576776)|Library exit0/93.05s; whole controller success, clean owned shutdown|
| Wasm Chrome |4/4|0f02a099 /[run40650621351](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40650621351)|Wasm exit0/310.10s; whole browser workflow remains failed on JS|
| JS Chrome |4/4|fa125cf3 /[run40652867059](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40652867059)|Library exit0/340.09s; whole focused JS workflow success|

**20 accepted target-method pairs, four authored scenarios.** All reports are fresh;
accepted cases have zero failures/errors/skips. All recorded inputs match their
own Git blobs (763/764/765/765/767 per respective snapshot); production date inputs
are identical/current. Source receipt is authoritative for exact inventory counts.

Browser wrappers immediately return the actual v2 TestResult/Promise, matching
the Compose1.12/Kotlin2.4 test adapters. JS additionally awaits real Skiko exports;
native Promise.then assimilates the returned Compose test Promise. No assertions
or failures are caught/discarded. Both browser XML timings are unusually short;
these are reported outcomes, not rendering/performance profiles or certification
of arbitrary native browser interactions. No confirmed Promise bypass was found
in reviewed support code.

## Preserve failed observations and owning fixture repairs

- The first host null-input fixture incorrectly treated the merged Material
  "Date" label plus editable value as wholly empty. The correction checks the
  actual EditableText field; other three scenario bodies remain unchanged.
- Early focused-dispatch/controller gates failed before accepted runtime evidence.
  Their original logs/receipts are preserved, not counted as passed tests.
- The first real JS browser attempt failed4/4 before dialog creation on missing
  Skiko raster exports. The recovered JS fixture imports/awaits real initialization.
- The Android APK initially rejected32 inherited common-test names with spaces at
  minSdk23. Identifiers changed only; assertions/annotations/bodies and minimum
  SDK did not. Compilation alone is zero runtime tests. A local wrapper typo
  failed before Gradle invocation and is retained as harness error.
- The accepted API35 emulator ran SELinux Enforcing and stopped cleanly. It is
  not a physical/minimum-Android camera/provider/permission runtime claim.

The [closure readback](issue-121-closure-readback.json) confirms closed/completed
and preservation of original title/body/labels. [Exact resolution comment](issue-121-resolution-comment.md).
Artifacts contain evidence only, not candidate packages. Source JARs and prior
report ZIPs are recorded by hash but not committed; none is executed as instructions.
Full iOS/native/minimum-platform, legal/dependency/security, consumer/ABI and
release gates remain separate. No packages, releases or deployments were published.
