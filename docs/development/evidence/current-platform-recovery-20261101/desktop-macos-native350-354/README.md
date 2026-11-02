# macOS missing-only request-state results — 2026-11-02

[Original run41517918952](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41517918952),
attempt1 at `54fe20a01b953ebd32f1fa85aa4f1b795ec5c41f`, remains **FAILED**.
Tooling passes; the two selected macOS hosts execute **4 native methods:
2 passed/2 failed**, four fresh original XML reports, zero errors/skips/N/A.
Unrequested sample/consumer jobs are not library acceptance.

| Actual host | Native result | Gradle exit / elapsed | JDK |
| --- | --- | --- | --- |
| macOS ARM64 | Request passes; Stop fails1/2 | 1 /326.93s | 17.0.21 |
| macOS x64 | Request passes; Stop fails1/2 | 1 /449.06s | 17.0.20.1 |

## Qualification and originals

[Solo review353](REVIEW353.json) accepts **48 passive source/results checks**, not
48 new tests. Exact original methods, architecture/JDK17/Gradle9.7.1, clean source,
fresh task/XML/receipts and owned cleanup qualify. All **four actual1,212-input
maps** equal frozen Git/dispatch/current source. [Map identities](actual-map-identities353.json)
bind each original path to the single preserved [actual map](actual-inputs353.json).
Two initially over-specific JDK check labels were corrected without changing
predicates/results; [original labels](REVIEW353-original-labels.json) are retained.

[Dispatch350](DISPATCH350.json), [once-only acquisition352](ACQUISITION.json),
[run/job summary](run-summary353.json), and per-host original plans, receipts,
runtimes, dependency/cache observations and XML are preserved in
[ARM64](desktop-macos-arm64/receipt.json) and [x64](desktop-macos-x64/receipt.json).
Full original ZIPs remain privately cached, with hashes in the acquisition receipt.
No acquired original archive was downloaded again. XML clocks are retained
separately from the Gradle elapsed times above.

Accept and **exclude from unchanged replay** on both macOS architectures:

`DesktopWebViewRequestStateAcceptanceTest.twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner`.

The genuine owned JavaFX/Compose navigator, two held/refused TCP requests,
native request-state/old-error reset, document/title/URL and same-owner recovery
assertions hold. No sample application substitutes for these library tests.
**Never dispatch the old macOS-pair profile again.**

## Both original public Stop methods remain failed

Both original failures report, before fixture cleanup:

```text
public Stop witness refused; sampled=true;worker=CANCELLED;running=false;finished=true;cancellations=1;peerEofs=0;pending=1;arrivals=1;responses=0;closing=false
```

The worker/library state cancels but the held peer remains pending. Original
ten-second/six-predicate acceptance is unchanged; recovery is unreached. Sequential
scalars are **not an atomic snapshot**, and the actual internal loader route and
instance are unobserved. The independently source-confirmed JavaFX flag-only
cancellation defect is consistent, not retrospective instance proof. Only an
owning correction and these **failed methods alone** can qualify recovery.

## Disposition and next work

[#64 progress6587820742](https://github.com/Apdelrahman1911/nativeCmpkit/issues/64#issuecomment-6587820742)
was posted once and read back exactly **before documentation**;
[receipt354](PROGRESS354.json) confirms original fields unchanged/state open.
This Desktop cohort now lacks only **Linux ARM64 Stop and both macOS Stops**.
Reuse accepted Linux/Windows/browser/iOS/Android cases, without replay. Ordinary
JavaFX dependency adoption, corresponding-source/legal/security/consumer/API–ABI
and all original issue criteria remain separate; private candidate success alone
does not activate a fix for ordinary consumers.

No OS-wide offline/DNS/TLS, internal-loader, native-heap, packaged-consumer,
API–ABI, legal/security or release certificate follows. Counts remain **97 closed/
75 open/172 total**; no new closure/publication. Both reservations are freed;
recheck global capacity before failed-only candidate dispatch. Continue solo,
serial local/8GiB reserve/max2 combined hosted-heavy including queued,
development only; publishing/Pages/main/history/readiness gates remain intact.
