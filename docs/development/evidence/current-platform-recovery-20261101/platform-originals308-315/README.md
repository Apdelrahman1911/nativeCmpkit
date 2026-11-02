# Focused Windows, Android and iOS original-result review

Source revision: `2c2e97a16affbb73aafaaddc7be5b918c880c041`.
The three original archives were acquired once and reviewed from those cached
bytes. No accepted native method was replayed for this review.

| Original run | Actual library result | Execution |
| --- | --- | --- |
| [Windows 41420619487](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41420619487) | **1/1 pass**, one fresh XML | Gradle exit 0 / 228.28 s; method 6.02 s |
| [Android 41421993681](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41421993681) | **0/2 pass**, two failures, one XML | Gradle exit 1 / 110.04 s |
| [iOS 41420816652](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41420816652) | **0/4 pass**, four failures, one XML | Gradle exit 1 / 1484.39 s |

## Windows: original public Stop acceptance, private candidate only

Only `DesktopWebViewStopRedirectAcceptanceTest.`
`publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner`
executed. The original ten-second/six-predicate gate, client EOF **before cleanup**,
zero response, same native owner recovery and Compose/FX/server cleanup remain.
Actual Temurin 17.0.20.1+1 / Gradle 9.7.1 / Windows x64 executed the public library
method, not just a standalone dependency probe.

The explicitly private full-JAR replacement has identity
`21.0.13-nativecmpkit-cancel1-local` and SHA-256
`39d44471da67d926afdf877b4a3349bde1d7830f10d197aa0cfb18fcd0998d43`.
The original runtime JAR was removed exactly once; the candidate was inserted
exactly once. No module patch, classpath shadow, private route override or cached
JAR mutation occurs. **Ordinary dependencies have not adopted this candidate.**

[Review311](REVIEW311.json) qualifies 34 passive source/results checks: actual
1,204 library and 16 candidate-owning before/after hashes match frozen Git/current
bytes; 14 packaging inputs hold; five class pins match prior accepted bytes.
Reported web inventory 548/542 retains the public module descriptor/native DLL;
only the top-level loader and manifest change. Java-source inventory 312/311
retains all other source members. These are reviewed producer reports; no actual
binary was uploaded for independent remote binary inspection. The existing
unnamed-module warning remains.

Reuse this accepted Windows method, do not rerun it. Other original Desktop and
browser/offline requirements, default dependency adoption, complete native
corresponding source, legal/security, consumer and API/ABI gates remain.
**#64 and #3 stay open.**

## Android: exact button-text mismatch and missing Downloads row observed

[Review314](REVIEW314.json) reads all four actual 1,204-entry before/after maps,
the finite stock API35 plan, registry fences, native XML and owned-emulator
cleanup. SDK/KVM/setup/APK and genuine device execution succeeded; grants and
public IO were **not reached**. The original suite `time="0.000"` is not a useful
duration; individual methods report 30.180 s and 21.575 s.

- **ExternalStorage / OPEN_TREE_BUTTON:** Google DocumentsUI with its exact
  admitted namespace; refreshed, visible, package-exact root and one node;
  node ID exact, node text not exact. Actual text/casing and the individual
  enabled/clickable values were not reported. Do not assume uppercase, normalize
  labels without evidence, or interpret compound zeroes as all operands false.
- **Downloads / OWNED_FOLDER_ROW:** one refreshed, visible, package-exact
  `dir_list`; the owned-text query returned zero nodes. The current provider/root
  location and the absence cause were not observed.

These are **after-timeout**, cooperative 1,000 ms observations, not historical
failed-poll operands or atomic native state. No native predicate or resource
admission was relaxed. Diagnose the owning harness before any further missing-only
request. **#55 stays open; cloud C1 is separate.**

## iOS: action accessibility gate still unreached

All four original methods fail in `activateImportantNativeAction` **before**
`accessibilityActivate()`. The app is active/key/attached, and each expected
UIAlertAction is unique/enabled. Complete UIView samples contain 36, 65, 35 and
36 views; all exact label/button/visible/eligible match counts are zero.

The public-container observer reads only the **first 16** UIView owners in each
sample. All 16 report zero count; `owner_prefix_truncated=true`, `unknown=true`
and `index_children=0`. It does **not** establish absence of accessibility
elements throughout the alert, nor their labels, visibility, attachment or cause.
No list getter, nested-container traversal or native action input was observed.

Main Worker 1 / owned Worker 2, runner exit 0, Worker termination, installed
identity and owned-app cleanup hold. Protocol 61.24 s / transport 61.26 s success
is **not JUnit success**. Do not use a manager/private handler/forced activation
fallback. **#28 stays open.**

## Review and current issue state

The final 50 passive checks in Review314 qualify the two failed originals,
not 50 tests. Initial reviewer expectations incorrectly stripped KGP decoration
from XML but not the receipt, and then used a non-extension source declaration;
both reviewer failures are retained in [corrections](reviewer-corrections.json).
No native/archive reacquisition or library-test replay followed those corrections.

[State315](STATE315.json) freshly reads **97 closed / 75 open / 172 total**;
#3/#28/#55/#64 remain open. Ledger states remain 22 implemented / 42 partially
verified / 95 verified / five unresolved. Today's [upstream snapshot](../../../upstream-refresh-20261102T050936Z/README.md)
already maps all 16 open Calf issues; no missing import or duplicate is inferred.
No additional upstream discussion/timeline acquisition is claimed.

Continue solo; serial local heavy builds, 8 GiB disk reserve and maximum two
combined hosted-heavy reservations **including queued work** remain. No packages,
releases, deployment, Pages, main integration or default dependency adoption is
authorized by these scoped results. All applicable security/readiness gates stay.
