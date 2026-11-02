# Desktop security CI fixture recovery — 381–384

## Original failure, not a native result

Run [41531273049](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41531273049)
at `bfb00ec87dfc980ac2f18591afcdd79e81909611` remains **FAILED**. Tooling ran
2,442 CI source methods in 129.845s, with one failure. The earlier 35/80/96
source-only groups passed. Profile selection was skipped; **zero Gradle,
Desktop native methods, XML or artifacts** followed. All six other jobs were
skipped. Originals were acquired once under an exclusive claim; the original
ZIP digest and all eight member identities are in `ACQUISITION382.json`.
`tooling-original.txt` preserves the acquired whole tooling log, not a new run.

The failure at the original
`scripts/ci/test_android_external337_fixture_recovery.py:187` compared the
External328 postimage digest `0f6c7a40…` directly with the newer live
`scripts/ci/library_tests.py` digest `d7b1e7b6…`. The admitted Stop-only change
has its own exact full-source inverse, but this one fixture forgot to compose
that stage. This is a **confirmed source-fixture defect**, not a macOS TLS,
rendering, cookie, JS or engine failure.

## Owning correction and important tests

Only `scripts/ci/test_android_external337_fixture_recovery.py` changes:

1. Admit exact live source through the existing
   `current_source_before_arm64_stop_candidate` before comparing its prior-stage
   digest. The original External328 manifest, all 16 bindings/49 fragments,
   expected pins and the ARM64 three-binding/eight-fragment inverse remain exact.
2. Continue passing **raw current bytes** to the actual historical-admission
   reader; an older image must not impersonate current source.
3. Add one owning-wiring regression refusing six old/changed/truncated/foreign/
   empty source variants. No digest refresh or source/native fallback.

**Only the one originally failed method plus the NEW method ran locally:
2/2 pass, zero failures/errors/skips, unittest 0.135s, wrapper 0.145196s.**
The six rejection variants are synthetic controls, not native executions.
`GREEN383.json` and the original stderr preserve results. All 1,215 input
identities stay held during the two methods. Compared with frozen dispatch381,
only this CI fixture changes; the other 1,214 inputs are byte-identical.

`REVIEW384.json` accepts 15 separate **passive** source/results checks. All
preexisting other methods/setup/teardown and production/native/Gradle/workflow/
permissions/XML admission remain unchanged. Both exact missing-only security
pair source preflights pass without builds; `preflight384.json` preserves them.
These are not additional runtime/security tests. The full hosted tooling gate
still needs to pass after this correction.

## Next and boundaries

After development-only commit/push and a fresh global capacity observation,
request the unexecuted macOS security pair once; only after it terminates, request
the Windows/Linux ARM64 pair. Each pair reserves both allowed hosted-heavy slots,
including queued rows. Do not dispatch the other pair against known-broken
shared tooling. Do not rerun accepted Stop/request methods or Linux x64 TLS/
unchanged graph/advisory populations. Other-host graphs must be real acquisitions;
query only genuinely new exact coordinates.

#64 and #144 stay open. The 13 security methods and differing host graphs remain
unaccepted at this preparation checkpoint. A fixture pass does not establish
native behavior, corresponding-source/legal/security, ordinary consumer adoption,
API–ABI, whole-platform or release readiness. No issue closure, publication,
deployment, Pages/main or imported-history change occurs. Work continues solo,
serial local heavy/8GiB reserve/max2 combined hosted including queued, read-only
verification tokens/all actions allowed/no mandatory SHA pinning.
