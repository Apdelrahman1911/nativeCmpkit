# Bounded installed-app registration observation proposal — no patch or retry

## Exact basis

Run **41242777493**, attempt **1**, at
`7380a04674c2dc83583a45953418ec2c823b4258` fails before a launch PID. Its one
owned console window is **2026-10-31T21:37:20.457753Z–21:37:22.901077Z**.
The existing single log query retains **102 events / 79 owned / 23 rejected**,
`service-delegate-denial`, and **NSOSStatusErrorDomain −10814**. The fixed code
is an observation, **not proof of an unregistered app, signing error, executable
error, simulator defect, or any other cause**. Do not repeat that log query.

Signing, signed iOS `get-task-allow=true` readback, installation, installed-byte
identity checks, and owned cleanup pass. The failure remains real: **zero PID,
activation, Worker, tests, profile recording/export/leaks**.

## What the frozen source does and does not establish

- `source/scripts/ci/ios_ui_application.py:204–217` constructs the fixed plist:
  exact source/session bundle ID, `CFBundleExecutable=NativeCmpkitLibraryTests`,
  `CFBundlePackageType=APPL`, simulator platform, and linked minimum OS.
- The generated 1085-byte plist deterministically hashes to
  `153eff8644c43588aeda06de711758e5999aaa18ad1141383988a413e633453b`, exactly the
  recorded installed/local plist identity. There is no evidence for adding or
  changing plist keys.
- `ios_ui_application.py:761–771` checks the returned installed app container,
  regular/unshared non-symlink executable and plist, exact hashes, and bundle ID.
  It does **not retain an explicit registration readback**, a registered-path
  correlation, or an installed executable permission/access observation.
  A successful container lookup is not discarded; without the running tool's
  implementation/schema, this review does not translate it into a separate
  LaunchServices-ready assertion.
- `ios_ui_application.py:1012` captures the exact Booted simulator before staging;
  `runtime_context.py:199–203` validates that actual selection and state.
  The app capture at **21:36:36.046640Z** precedes console launch by about **44.41 s**.
  No post-launch capture occurs because transport fails first.
- `ios_ui_application.py:1048–1057` performs install and installed identity;
  `:1058–1070` prepares the profile; `:1072–1076` performs the one genuine launch.
  No registration-specific query is present in that interval.
- `apple_image_profile.py:209–213` independently observes the exact selected
  simulator once in `xctrace list devices`; that is not launcher registration or
  an Instruments recording.

**The smallest missing independent fact is an exact owned app registration
observation correlated to the already-verified installed container. Registration
state is unobserved in the retained evidence, not proved missing.**

## Minimal future candidate, only after lead approval/source review

1. Establish the **running same-Xcode SDK's supported interface and output
   serialization** with one bounded read-only capability/help observation.
   An exact-bundle `simctl appinfo` interface would be narrower than `listapps`.
   **Neither interface's support/output schema has been observed by this review.**
   Do not assume JSON, plist, OpenStep, key names, a `--json` flag, or a success
   schema. Unsupported/unknown shape stops for review; there is no automatic
   `listapps`, registry-file, private-API, alternate-simulator, or logging fallback.
2. If the actual supported interface has an exact-bundle selector, make **one**
   capped read-only query for the existing selected simulator UUID and the fresh
   source/session bundle, after successful install identity and before launch.
   No new app launch, reinstall, boot/reset, database mutation, permission change,
   entitlement, or broad log query. Do not read other apps' records.
3. After actual schema review, retain only fixed semantic facts: exit code and
   byte/hash bounds; exact bundle registration found/missing/unavailable; whether
   its registered app path equals the already-verified container; and, **only if
   supplied by the actual schema**, whether the registered executable identity is
   the exact expected installed executable. Raw registry/plist/path/inventory
   contents never enter artifacts or messages. An unknown field is unavailable,
   not fabricated or silently accepted.
4. Reuse the existing installed file/hash/plist and source/runtime witnesses.
   A local nonmutating installed `X_OK`/permission boolean could fill the small
   file-metadata gap without changing permissions. If the lead requires a
   launch-adjacent selected-state observation, use the existing supported
   `simctl list devices --json` parser and retain only the exact selected record;
   do not recapture unrelated compiler context or guess an unobserved filter.
   These are optional additional diagnostics, not substitutes for registration.

If the running SDK offers only `listapps`, a separately reviewed bounded exact-key
selection would be needed; that is **not** an authorized fallback in this proposal.
The command and schema decision remains with the lead. No candidate code was
written and no actual help/app-registration command was executed here.

## Required refusal/ownership boundaries for any later implementation

- Exact source/session bundle equality, not prefix/suffix/substring or basename
  matching; no duplicate/ambiguous registration.
- Strict bounded parser for the **observed** serialization; refuse truncation,
  duplicate fields, unsupported structures, and nonfinite values where relevant.
- Unknown/nonzero tool outcomes do not mean absent registration or authorize
  mutation/retry. Registered path disagreement never permits foreign cleanup.
- Preserve original installed-byte and foreign-app refusals. A failed diagnostic
  cannot suppress the already-owned cleanup or turn the existing failure green.
- Keep genuine UIKit launch, real protocol/Worker/testcases, exact fresh XML,
  same-PID Instruments/allocation-frame/leaks gates, and ADR0012 signing scope.
  No timeout increase, launcher-flag change, plist repair, environment repair,
  bundle-ID change, automatic dispatch, or accepted-suite replay is supported by
  this evidence.

## Disposition

**Cause unknown. #141 remains unverified/open.** Prior strict startup
**40989310808**, profile timeout **41008502211**, and other pre-PID failures remain
failed/unfixed/unwaived. This proposal supplies no native, heap, attachment,
consumer/ABI/dependency/legal/security/publishing/release clearance.
