# Private #64 iOS metadata protocol — owning weak-identity revision

**Prepared and source/synthetic reviewed only. Not integrated, compiled, native-accepted, released or issue-closed.**

This replaces, but does not modify, the previous sealed proposal `8ae51331fb9213aba015b82378b3ac3d50462aa7c3b18558c2d938f3ee2d94b8`. The lead alone owns integration, Git/source maps, real Mac compilation, immutable verification requests and any issue disposition.

## Exact delivery and owning correction

- Two existing iOS-only production paths, **19 exact single-occurrence commuting fragments over the original root preimages**, and two new Python source/synthetic guards. `DELTA.json`, `FRAGMENTS.json`, `PATCH.diff` and `afterimages/` are the complete replacement delivery.
- `WEAK-REPAIR-FRAGMENTS.json` records the **six** minimum changes over the previous sealed production proposal. The original archive remains intact. Apply only one chosen exact delivery; never guess offsets or silently combine already-applied fragments.
- A passive independent review found a source-conditional hole in the previous proposal: after three captured issued handles A→B→C, the state retained only C and predecessor B. A delayed start(A) could therefore be treated as a new native start and replace C. **The new three-issued source and model controls first fail against that previous sealed proposal, then pass the owning revision. This is not evidence WebKit delivered that order or that it caused the actual failure.**
- The revision adds native `NSHashTable` membership with `NSPointerFunctionsWeakMemory` and `NSPointerFunctionsObjectPointerPersonality`. Current live navigation identity is checked before known-old refusal. Every captured non-null URL/HTML/Reload return enters weak membership while the view is still owned, even if its internal request record was reentrantly replaced. Only the still-current record can bind; binding cannot reopen a phase or overwrite an already-observed newer start.
- An unmatched live handle already registered in that table is refused. An **unseen** genuine native start remains adoptable in all original phases, including during active loads. Accepted non-null starts enter membership before the phase transition/common reset. This does not blanket-disable native links or Back/Forward. The original native Back/Forward call bodies remain exact.
- Only the original current-owned final release stage clears weak membership and the strong current/predecessor references. Original cleanup order, first-failure preservation, native-view ownership, observer, native host/Worker/presenter, request/DNS/lifecycle tests and public/common production declarations remain unchanged.

## Retained phase and metadata protocol

The previous proposal's six internal phases remain: AwaitingStart, Provisional, Committed, FinishedCommitted, FinishedUncommitted and SuspendedCommitted. Owned URL/HTML loads invalidate publication before unchanged common `acceptContent`; unsupported/invalid inputs finish uncommitted and preserve their original errors. NavigatorOnly remains a no-op. A matching non-null current provisional start invokes unchanged `beginRequest`; a current unstopped Provisional→Committed transition is required to publish document metadata. Finishing without commit cannot publish a successful document.

Title/URL KVO still requires a current committed witness **and native idle**. Loading/progress KVO and nil callbacks cannot create a commit. Successful idle same-document/history/fragment/title updates remain enabled. Loading following a finished commit suspends KVO publication without prematurely clearing errors before the actual new start. Current active failures retain the exact original native NSError code/description; no fabricated cancellation, post-failure field-clearing substitute or success is added. Reload uses native current URL, not stale declarative content.

Bound-record precommit Stop retains that navigation identity for its actual error while refusing later commit certification. Postcommit Stop preserves the committed document. The original current-view nil-finish bridge remains loading-only for an untracked owner. The prior phase model/helper definitions are byte-identical; the new synthetic extension refines binding/start/release bookkeeping only.

## Explicit limits — not a generalized native callback history

1. **Membership is only captured non-null URL/HTML/Reload returns and accepted non-null starts.** Discarded Back/Forward returns and ignored unmatched terminal/commit callbacks are not silently registered. The table is not described as every issued or every observed WK callback handle.
2. An unseen callback before its initiating native call has returned cannot yet be known-issued. The revision does not invent authority to associate that unknown handle with a reentrantly replaced request, arbitrary action order, URL, timestamp or pointer ordering.
3. The state retains at most current/predecessor strong navigation references. Additional membership is **native-lifetime-bounded weak storage, not a fixed cardinality/memory bound**. No navigation objects are deliberately retained by the table; no addresses are exported/cached. Native weak-zeroing, deallocation timing, storage compaction and actual Foundation behavior are not runtime-verified here.
4. SuspendedCommitted witnesses tokenless native loading before any new navigation identity. **Stop for that unidentified interval is outside the bound-record precommit Stop guarantee.** No guessed stopped flag is carried into the next genuine link. If a literal original criterion requires that separate interval, closure must remain held for its own justified protocol/evidence.
5. SuspendedCommitted has no loading=false recertification. Idle same-document behavior is source-preserved; arbitrary same-document native-loading cycles are not proved. A nil returned navigation is neither a fabricated error nor a terminal-completion guarantee.
6. Local pre-existing iOS simulator Foundation metadata passively confirms non-generic NSHashTable constructor/options and addObject/containsObject/removeAllObjects signatures, including ULong option types. This is **symbol/type readback only**, not SDK header acquisition, Foundation execution or real Mac Kotlin compilation. Platform compile/runtime remains required. No private SDK/metadata binary is delivered.

## Affected guards and bounded outcomes

No live existing CI guard adaptation or production-hash pin widening is needed. Exactly these three affected source-owning methods were executed **once each**, privately, and pass:

- `IosWebViewNativeIdentityTests.test_native_callbacks_match_the_retained_objc_owner_not_a_kotlin_wrapper`
- `IosWebViewNativeIdentityTests.test_identity_compares_live_native_pointers_and_nulls_never_form_a_lease`
- `WebViewIdentityRecoveryTests.test_final_ios_release_detaches_owned_view_before_owner_reset_and_keeps_failed_parent_predicate`

The prepared phase guard's `IosCurrentRequestMetadataSourceTests.test_source_live_identity_transition_and_noncommit_paths_are_bound` needed one constrained adaptation because the old adjacent null/current-record gate is now deliberately split around weak bookkeeping. It still requires native-owner/null refusal first, weak registration before replaced-record refusal, record refusal before binding, and no phase reopening; all original native/common pins and other assertions remain. That affected method freshly passes **1/1**.

New weak-extension controls pass **10/10**: three source and seven synthetic methods. The two three-issued regression reds against the previous seal are retained. Seven new unsafe mutated inputs are refused: strong memory, value personality, lost reentrant key, current-token blacklisting, missing accepted-start key, foreign-release clearing and null-key admission. Six are assertion refusals and one is a missing-source-marker shape refusal. No existing source owner was rerun for these mutations.

This revision has **14 green executions**, two preserved source/model regression reds and seven new unsafe-input refusals. The original seal's 24 green/one red executions remain original records, not fresh runs. Its sixteen phase model methods are reused on seven exact-byte model/helper definitions, not replayed; the three untouched prepared phase-source methods retain exact selected blocks/pins. There are 30 newly authored methods across the two prepared guards, not 30 native methods. All private selected runs refused subprocess/Git/build/acquisition/native/network calls. The unchanged full CI suite was not executed or claimed.

Exact readback holds **21 original source inputs / 19 unchanged non-delta paths**, including native request/DNS/lifecycle, actual host/Worker/presenter and ownership helpers, request fixture/controller and existing guard bytes. All root preimages still match and both new guard paths remain absent. The 19 full original fragment intervals are disjoint, all 171 unordered pairs commute, six complete orders match and inverse replacement restores both original files. The six incremental changes likewise commute in all 15 pairs/six orders and invert exactly. These are source transformations, not native acceptance.

## Actual evidence and next finite request

Actual iOS **41276065062 remains overall FAILED**: original request2 failed; disjoint genuine DNS1 was independently accepted only on its original run/inputs. The TLS source63 and held-redirect `assertStarted` source155 failures concern null final URL; the actual value, writer and callback/KVO order were not captured. No actual logs/artifacts/XML were reacquired, no failure was reclassified and no accepted DNS/native/host result was replayed. Unconditional provisional/retained metadata publication in the original source is a source finding, not the proven actual writer.

After lead-owned integration and required review/platform compilation, request **only original request2**, using existing `ios-webview-request-state` / `webview-ios-native-request-state`; no DNS1 or old lifecycle/host/native replay or assertion/hash/selector weakening. This proposal proves ZERO new Kotlin/compiler/Apple/WebKit/native/XML. #64 remains open, and every-target/offline/DNS/TLS, native/consumer/ABI/dependency/legal/security/readiness, publishing/Pages/main/history, serial-local/≥8GiB reserve/max2 combined hosted-heavy gates remain unwaived.
