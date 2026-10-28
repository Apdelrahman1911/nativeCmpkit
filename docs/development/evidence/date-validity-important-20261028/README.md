# Explicit date-validity acceptance — 2026-10-28

**UI-008 / [#158](https://github.com/Apdelrahman1911/nativeCmpkit/issues/158) is verified and closed.**
Both [original criteria/source/results review](direct-closure/important-result-review.json)
and [direct closure readback](direct-closure/closure-readback.json) preceded this
bookkeeping. Upstream [#541](https://github.com/MohamedRejeb/Calf/issues/541), original
finding and issue body/title/labels/history remain preserved; no upstream mutation.

## Important tests

Immutable **`8f5bb6f299ce017e2722529a43488408c7d2062c`**, Linux/Xvfb/JDK17:
[**4/4 actual methods**, one fresh XML](first001/receipt.json), zero failures/errors/skips,
exit 0 / 36.01 seconds. Three exercise actual production state/public validity API
and search/bounds; one renders the public compact picker with an actual Compose/Skia
library-level consumer. All 758 unchanged input hashes matched exact Git blobs,
and every XML testcase/hash was reviewed. Only this class ran, not an unrelated suite.

1. **Retained selection + validity:** NoDates retains March15 but reports false;
   null also reports false. Compatibility does not require silently clearing a value.
2. **Sparse rules:** a sole accepted date 367 days away is outside the default
   366-day search and does not validate the retained date. Explicit 367-day search
   and caller assignment reach that exact valid date.
3. **Ties + bounds:** later March16 wins a March15 tie over March14. Tightening
   maximum chooses March14; an effective window allowing no candidate retains it
   as invalid. Widening bounds restores March16 and true validity.
4. **Actual consumer integration:** valid→invalid→empty→valid drives localized Arabic
   text, polite live-region and state-description semantics. Actual pointer input
   on disabled submit produces no callback; valid clicks each submit once. The
   public predicate updates actual Compose reads, not a copied test-only validator.

## Chosen compatibility-preserving policy

`AdaptiveDatePickerState.isSelectionSelectable` is the additive observable API.
The existing selected-date value and bounded search are retained. A non-null date
must satisfy current year/date rules to return true; null returns false.
**Do not use the picker as sole business/security validation.**

The library does not invent application-specific translations or announcements.
A host should derive its localized valid/invalid/empty status from the predicate,
expose an appropriate `liveRegion`/`stateDescription`, and validate again at the
business-operation boundary. The test fixture is proper library consumer coverage,
not an existing sample application or a claimed built-in announcement.

## Evidence and limits

[Manifest](archive-manifest.json) binds original/archived hashes. Derived XML retains
all identities/outcomes, without private console/classpath bodies; quarantined
prior XML is not accepted as new execution. No production/API rewrite or test
assertion relaxation was needed to verify the implemented contract.

This is **not** UIKit/Android/browser presentation or recorded spoken VoiceOver,
Switch Control/keyboard, minimum-platform, native-memory, consumer/ABI/dependency/
legal/release certification. Those original distinct issues/gates remain.
No packages, releases, deployments, Pages or subagents.

**40 GitHub issues verified closed; ledger: 55 implemented / 65 partially verified /
36 verified / eight unresolved.** Continue important owning tests, review actual
source/results, close directly, then record evidence; no unrelated suite replay.
