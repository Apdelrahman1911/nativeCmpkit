# Shared pre-platform CI fixture repair — 2026-11-03

Both targeted requests at `b5fb998dea9603443629e48dda34813d34d74428` remain
FAILED, before profile selection or any Gradle/Apple/native execution:

- [memory2 /41566701746](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41566701746):
  CI source2507/137.358s, seven failure records across two methods.
- [XCUI iPhone7 /41566720024](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41566720024):
  CI source2507/133.087s, the same seven records/two methods.

[Once-acquired metadata and exact reviews](originals/) preserve both originals;
there are **ZERO native cases, XML, artifacts, compiler or selected platform jobs**.
The earlier weak-reference native failures are not replaced by these tooling failures.

## One owning patch for both requests

1. `test_android_external337_fixture_recovery.py:213` expects the exact newer
   XCTest/input refusal category. Its six malformed/preimage payloads already
   refused before historical digest evaluation; only the stale expected category
   was wrong. No live admission predicate or manifest pin is loosened.
2. `test_apple_appinfo_shape_route.py` selects the **unique exact WK finally guard**,
   not `finalbody[0]`, which now belongs to independent native-input cleanup.
   The original WK cleanup body hash and all help-only/upload assertions remain.
3. Two new synthetic AST controls verify stable selection with other owners and
   refusal of missing, duplicate, nested or changed guards; no normalization,
   first-match fallback, SDK or native execution.

[Only failed2+NEW2](local/important-four.json) pass4/4 once:
unittest0.251s /wrapper0.5638690800406039s. All1,246 before/after inputs hold;
only two owning fixture files differ and one new test file is added. All1,243 other
prior inputs, native Kotlin/Swift/project/controller/workflow/dependencies and old
inverse pins remain exact. **Reuse both applicable KLIB compilers and accepted
controls/native subsets; do not replay them for this test-only patch.**

First local cached-log inspection had a syntax typo before reading any bytes;
corrected cached-only inspection does not reacquire originals or execute tests.

Next push development only, then request only memory2 and XCUI iPhone7 within two
combined hosted reservations INCLUDING queued. They have not yet executed natively.
All five related issues stay partial/open;98closed/74open, ledger22implemented/
41partial/96verified/5unresolved. SOLO/serial-local/8GiB; read-only Actions/all/no
mandatory SHA pinning. No release/package/deployment, Pages/main/history or
legal/security/consumer/API–ABI/readiness gate is waived.
