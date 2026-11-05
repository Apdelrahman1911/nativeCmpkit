# Windows Vanniktech signature observation prerequisite (734-r2a)

This isolated, development-only patch adds one bounded, previously-unfollowed
`pom.asc` observation. It does **not** admit dependency bytes, signatures, keys,
consumer graphs, native functionality, or a release.

## Review and tests

Reviewer742 and the lead cleared the exact privacy-corrected observer and tests.
Only header/report privacy logic, NEW13/NEW20 and coupled source pins changed
from the preserved R2 proposal. The original R2 privacy refusal remains valid.
The unique FIRST cohort passed **22/22**, zero skips/failures/errors, once:
0.910s suite, 1.0348944200668484s enclosing protocol, child/supervisor exit0.
Five input/model full10/hash identities held; owned child/captures/model cleanup
passed. Saved results were independently accepted without replay.
`FIRST-NEW22-source-control-result.json` and `NEW22.stderr.txt` retain originals.
These are source/fake controls, **not actual Windows execution**.

## Actual prerequisite and privacy boundary

The accepted earlier observation was run42087525896/attempt1 at20523c4f431d,
job127456535149/artifact13443631641: source18 GETs returned303; only the
predeclared POM route was followed. That is not signature or graph acceptance.
This successor allows exactly one previously-unfollowed signature GET, no
redirect hop/fallback/retry, no query/credentials/wrong origin. Limits remain
90s total/60s acquisition/15s cleanup/20s IO, max1 request, 512KiB body and
65536B captures. New server Location values are **count/digest only**, with
public_Location=null. Only public JSON receipts are uploaded; raw body and
private worker streams remain ephemeral and uninspected, unavailable after
runner teardown. Any byte-pair/key/crypto review needs a separately qualified
same-owned-job stage or secured transfer; this patch authorizes neither.

The owning Job/GO/file-identity/deadline/cleanup protocol is unchanged.
The workflow changes only the observer command and public-artifact path.
Minimum contents:read, persist-credentials:false, no publication/deployment.
No old accepted controls, GETs, native/consumer populations are replayed.

## Issue and release disposition

#64 is NATIVE-005 WebView request-state reset, not dependency trust. Its original
fail/success/reload/stop/redirect/platform criteria remain **OPEN**. #40 and #3
retain their original trust/consumer/native/release criteria. No issue closure
or publishing readiness follows from this prerequisite. Hosted results must be
authenticated against the newly frozen immutable branch HEAD before use.

## Lead staging recovery

The first policy-preparation snippet refused at Python parse time (non-ASCII
byte literal), before policy writes. Explicit Git staging then admitted the five
source paths but refused the four new documents outside the sparse checkout.
Only the failed policy preparation and explicit sparse-aware document staging
were corrected. The completed source adoption and accepted NEW22 were not
reapplied or replayed; sparse checkout was not expanded.
