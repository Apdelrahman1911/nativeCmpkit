# Android permission/lifecycle — source-only batch

This isolated batch prepares three proper library-level Android API35 methods:
real approximate/precise and foreground/background permission dialogs; Settings
grant/repeated resume/disposal; and notification Settings revocation. A signed,
separate-UID helper supplies genuine OS dialogs and Settings actions. Tests require
the same PID, Binder, service and Activity generation plus agreement with public
single/batch library states. Restarted apps, manufactured callbacks or AppOps
changes cannot substitute for resume. Sample applications are not used.

## Adoption and source security

- Eighteen exact paths: six existing files, 36 reversible fragments and twelve
  additions. Lead admitted already-prepared, matching isolated postimages after
  verifying six HEAD preimages/inverses and twelve untracked additions; **zero
  source rewrites**. One mode-only correction preserves canonical storage-probe
  `0644`; five existing `0600` modes and twelve new `0644` modes are retained.
- Malformed XML is converted into bounded fixed-message `ValueError` failures
  without raw XML or exception-context leakage. A rejecting XML TreeBuilder
  also refuses encoded DTDs, including UTF16 input that bypassed lexical checks.
- Independent final review: [`review712-successor/ESSENTIAL-REVIEW.json`](review712-successor/ESSENTIAL-REVIEW.json),
  SHA-256 `c590f5dca1b188a4f26cf2a55067db8743a1a1049965bd78c3679bfbe9d5d02c`.
- Lead adoption: [`lead716/ACTUAL-SOURCE-ADOPTION716.json`](lead716/ACTUAL-SOURCE-ADOPTION716.json).
  The ROOT producer/Camera/Android cohort is unchanged.

## Saved execution chronology

The original RED14 remains failed. Implemented14 + NEW9 passed **23/23 once**.
After two XML defects were found, NEW3 + affected5 passed **8/8 once**, 0.080s
suite, all 43 inputs held. Independent review accepted 251 passive source/custody
obligations. Neither accepted population was replayed; this is not a fresh26 or
combined31-test run. XML review occurred **after** FIRST8: no independent
pre-GREEN qualification is claimed. The original outer capture-wrapper source
was not separately retained; saved child argv, selections, results, clocks and
before/after maps are preserved, not replaced by a reconstructed wrapper.

## Outstanding original criteria

**Zero compiler, planner/controller, live Android or native outcomes.** Issue
[#19](https://github.com/Apdelrahman1911/nativeCmpkit/issues/19) still requires
API23/29/30/31/33+ and current/legacy targetSdk combinations, omitted-manifest and
disabled-services distinctions. [#107](https://github.com/Apdelrahman1911/nativeCmpkit/issues/107)
still requires other Settings revocations and one-time expiry, plus any remaining
original lifecycle/disposal criteria. API35 preparation is not whole-issue
acceptance. See [`packet/ORIGINAL-CRITERIA.json`](packet/ORIGINAL-CRITERIA.json)
and the finite [`packet/NATIVE-VERIFICATION-PLAN.json`](packet/NATIVE-VERIFICATION-PLAN.json).

Qualify current branch tooling and compiler inputs before finite missing-only
requests; inspect fresh original XML, OS/public behavior and owned cleanup. At
most two combined hosted reservations include queued work; local heavy builds
require 8GiB disk and 6GiB available compiler memory. All compatibility, API/ABI,
consumer, legal/dependency/security, publishing/release/Pages/main/history gates
remain. The 144 byte-identical archival records and `SHA256SUMS` retain failures,
source recipes and review evidence, not authorization to execute archival scripts.
