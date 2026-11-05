# Actual Windows verification after the owned-response EOF fix

The [owning EOF source fix](../windows-owned-eof-after770/README.md) is now
verified by two **new Windows executions**, not only by the earlier local
socketpair regressions. Both used commit
`32e834be14715519e96f094c61d26797fbd9522c` on the isolated
`development/javafx-ordinary-consumer1` branch.

## Accepted results

| Scope | Run / attempt / selected job | Actual result |
| --- | --- | --- |
| Fixed original row 0 | [42048537238](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42048537238) / 1 / 127318049405 | SUCCESS; one request, HTTP 200, 9,034 bytes, genuine EOF and public-text qualification; 18 source inputs held |
| Normal observation plan | [42051371077](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42051371077) / 1 / 127328052322 | SUCCESS; 120 attempted, 58 complete/public-text-qualified responses, 18 HTTP 303 and 44 HTTP 404 refusals; 17 source inputs held |

The normal worker completed in **26.312s**, controller in **26.578s**, child exit
0. The protocol, source intent/before/after identity, all 58 owned write-close
receipts and seven owned Job/child/runtime cleanup records were accepted. Each
run's other three jobs were terminal, zero-step skips; neither requested an
ordinary Gradle consumer or a native Stop test.

Normal public observations comprise 19 POMs, 7 module descriptors, 9 SHA256
sidecars and 23 armored signatures; 437,107 raw body bytes were observed. The
62 refused rows are **explicit gaps**, not successes, retries, redirects or N/A.
The unchanged no-redirect observer did not follow any HTTP 303.

## Original evidence and independent review

`one-row/` and `normal120/` preserve the three validated public JSON reports,
authenticated run/job and artifact metadata, one-download digest receipts,
terminal reservation releases and independent 734 acceptance records.
`SHA256SUMS` binds their archived bytes. No private response body, child stream,
artifact ZIP, credential, key or new trust policy is exported here.

| Artifact | ID | ZIP bytes | Authenticated SHA256 |
| --- | --- | --- | --- |
| One row | 13425458366 | 7,714 | `b0a62bbd3101143433fa0d06382416452e09e6cc8cd9ff8de0d8d7bf7ff71e66` |
| Normal 120 | 13425903765 | 67,279 | `17939f8e6f3dc2d6f89b96dcb1fb93b48b4dd7bf42f2615df471854ed2e555ae` |

Accepted local EOF regressions and source reviews are reused, not executed
again. Earlier refused/failed runs remain unchanged. The first run's CLI
correction and the independent review's truncated-display observations are
preserved as instrumentation history; neither is a hosted test failure.
Original normal-run failure causation remains **unknown**.

## What this does not establish

This verifies the changed observer's real Windows transport, EOF and owned
resource cleanup. It does **not** verify publisher signatures, independently
anchored provenance, complete bootstrap/transitive graph, Gradle policy
enforcement, compiler, ordinary consumer, native library behavior or release
readiness. Nine matching registry checksums are same-registry integrity only.
`REVIEWED_EXPECTATIONS_SHA256` remains `None`; `NO_ADMISSION` remains unchanged.

**#64 and #40 remain open** for their original consumer/dependency requirements.
Do not dispatch the unchanged ordinary consumer or replay accepted private
Windows Stop. Next obtain official publisher/key/source anchors, complete both
ROOT and standalone-consumer dependency closures, and verify both real policies
including negative enforcement before consumer execution. No publication,
release, deployment, main/history mutation or security-gate waiver follows.
