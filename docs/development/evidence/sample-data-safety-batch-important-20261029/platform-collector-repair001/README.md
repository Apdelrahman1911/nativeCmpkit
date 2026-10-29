# Shared sample collector repair and no-replay app recovery

[Linux postmortem](../platform-linux-ci002/postmortem001/review.json) independently
reviews **50/50 actual sample methods** (Android-host16, JS17, Wasm17 /15 XML)
and all four real compile graphs. Whole40963671526 remains **FAILED**: the sample
caller passed its `required_testcases` to an unfiltered library plan. The owning
library filter guard correctly rejected it. No source-after/process-exit/output
receipt survived; no all-app-build or library/native/release success is inferred.
The preceding collector's zero is zero accepted durable invocation receipts,
not zero actual XML methods. Its original review is retained unchanged.

The minimal sample adapter uses the shared safe XML reader with only report
metadata, then independently enforces its complete source-derived exact method
inventory. Library filter rejection remains intact. Parse refusals produce an
explicit failed receipt with final input checks; a durable process receipt is
written before reduction. Five new owning boundaries include the real shared
parser, failed-receipt/cleanup, unchanged library filter policy, and explicit
build-only CLI/workflow scope. No parser assertions were relaxed.

[Final important tooling](final-important001/review.json): **84/84 synthetic
methods**, all960 inputs held, actionlint1.7.12 and whitespace pass; zero local
Gradle/native/sample executions. Earlier three reds, first16/15pass/one registry
error and full1745-method run/four error events in two host-capacity-dependent
synthetic methods are preserved. That full run remains failed. Only parser-case
fixture capacity is mocked; production and negative8GiB guards are unchanged.
Counts overlap earlier73/broad runs, not additive unique methods or native tests.

Finite `sample-builds-linux`/`sample-builds-apple` requests retain every actual
app/framework/dependency task and real unsigned Xcode shell integration, but
request and count **ZERO tests**. This recovers missing build evidence without
replaying50 completed methods (or any later completed Apple methods). All11
library/device slots stay intact; sample evidence never substitutes for library
coverage. #100/#154 remain open until their own original criteria pass. Preserve
all historical attempts; never rerun a dispatcher with dispatch-attempt.json.
Single-agent / max two combined heavy requests /8GiB reserve; no packages,
releases, deployments, Pages, main/history rewrite or independent-gate waivers.
