# Living CI/build documentation: exact proposed addenda

The shared files were **not edited**. `observed-docs/` preserves the two reviewed
document versions; `suggested-changes.json` records their hashes, stale-claim
locations and the hash of `proposed-addenda.patch`. The lead should check for
intervening edits before integrating that patch rather than applying it blindly.

## What was independently checked

`receipt-reconciliation.json` binds the actual receipt, archive, runtime, plan and
log bytes. Every archived report hash was checked against its archive inventory;
the corresponding original report digest was reconciled to the producer receipt.
All 69 sanitized XML files were parsed without DTD/entities, and actual testcase,
pass/failure/error/skip counts were reconciled per report and in aggregate. The
four runs' source-input maps and canonical input digests were equal before/after.
Runtime receipt hashes and exact fresh-task markers were checked. Sanitized XML
is not relabeled as original raw XML, and no later mutable build output was used.

| Existing execution | Exit / elapsed | Independently checked scope |
|---|---|---|
| First library desktop command | **1 / 59.01 s** | UI and NAV test compilation failed; whole command stays failed. Later receipts do not revise it. |
| `ci-helper-smoke-001` | **0 / 71.02 s** | IO-only desktop, 22 passed cases, 5 reports, 688 stable captured inputs, explicit subset |
| `js-full-001` | **1 / 580.12 s** | Full request for 19 modules; 18 actually ran. 267 cases, 265 passed, 2 failed, 46 reports; 691 stable inputs. Share test compilation failed, with no task marker or testcase. |
| `js-focused-002` | **1 / 80.01 s** | Three-module subset, 83 cases, 82 passed, 1 failed, 12 reports; 691 stable inputs. NAV 36/37 passed, share 17/17, WebView 29/29. |
| `nav-desktop-002` | **0 / 38.01 s** | NAV desktop subset, 51 passed cases, 6 reports; 691 stable inputs, not a JS fix or whole-library pass |
| `yarn-materialization-003` | **0 / 122.03 s** | Explicit JS/Wasm project-lock bootstrap; 701 existing inputs unchanged plus 2 new stored locks; **zero tests** |

The helper runs used Linux x64 and JDK17.0.20, with dirty source at base commit
`94d2492e99d5cbc060409d94d9f88febd06222d5`. Browser runs used Chrome 153.0.8010.36.
The full and focused JS source digests differ; repeated common methods and
overlapping suites must not be summed as unique coverage or a complete green run.
The helper's 688/691-input scope is smaller than the lead's expanded 700/703-input
capture because the latter additionally includes 12 notice/identity inputs.
That collector-scope distinction does not assert that separately timed snapshots
contain otherwise identical source bytes.

Specific preserved failures:

- Initial desktop: unresolved `supportsProgrammaticNativeMenu` in the UI fixture
  and Kotlin generic inference/reified-intersection errors in NAV tests.
- Full JS: NAV `primitiveArraysRoundTripNullEmptyAndValues`; WebView
  `scriptEnabledIsolatedHtmlCannotMutateParentDom`; share test generic inference
  failures prevented any share test invocation.
- Focused JS: NAV
  `unsupportedPayloadsAndSchemaOnlyNavigationArgumentsFailBeforeMutation` failed.
  Share and WebView passed their actual cases, but the command still failed.

These are observations of those revisions, not claims about later repairs.
The detailed source causes belong to the subsystem's own evidence; a SecurityError
in a test is not by itself a demonstrated sandbox escape.

## Minimal living-document corrections

The unapplied patch proposes only:

1. Replace CI README's “fresh-tests/full runner have not yet executed a real
   Gradle test task” with the actual IO/NAV successes and JS failures above.
2. Make BUILD.md's historical 39-Python-test row describe that **specific synthetic
   invocation**, not claim the helper has still never executed anywhere.
3. Add four receipt-linked helper-result rows after the preserved first desktop
   failure, without rewriting the historical failure or offline fixture counts.
4. Expand the already-correct bootstrap003 paragraph with its exact zero-test
   scope and lock limitations; replace the stale closing “not ... real
   helper-test evidence” statement while retaining the absence of hosted proof.

No changes are proposed to the template's inactive status, owner-controlled
Actions policy or native host-N/A rules. The ten hosted slots have not been
established by these local runs. Device/instrumentation status should be updated
separately after the lead's current device invocation has terminal evidence;
these named receipts cannot prove that result.

## Bootstrap limitations intentionally retained

The stored JS lock has 438 registry resolutions with SHA512 integrity and one
exact Kotlin/karma VCS commit with no lock SRI. The Wasm **project** lock has two
registry resolutions with integrity; bootstrap003 did not initialize or verify
the separate Wasm browser-tooling lock. Its first post-build collector's
restrictive-origin rejection is preserved, distinct from the successful Gradle
producer result.

Archived stored-lock hashes were checked, not current generated cache contents.
Acquired integrity values are TOFU metadata, not independent publisher trust.
Later JS execution does not prove ordinary frozen-install behavior, the VCS
tarball's independent byte integrity, or a complete Wasm/platform/runtime matrix.
No new command was run to change those states during this review.
