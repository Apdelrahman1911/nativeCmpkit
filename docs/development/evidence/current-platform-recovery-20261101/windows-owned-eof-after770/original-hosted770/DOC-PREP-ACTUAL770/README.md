# Windows one-request diagnostic — actual hosted result

On 2026-11-05 the exact diagnostic profile ran once on Windows 2025 at
`b2fdb17fe2107af6fef0cc3e3ee13df1bb757b00`:
[run 42040119698, attempt 1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42040119698),
job `127288430984`, artifact `13419967757`.

The owned diagnostic protocol passed. Exactly one request was attempted; the
unchanged original plan still contains 120 requests. The direct child exited 0,
source18 remained unchanged, the Windows Job was terminated/empty/closed, and
owned empty runtime directories were removed. This is **not consumer verification**.

The HTTP response was **refused**, despite HTTP 200 and 9,034 captured bytes.
The actual primary operation was `transport-settimeout-body` with `errno=10038`
and `winerror=10038`; there were no recorded cleanup errors or overflow.
`complete_response` and `public_text_qualified` remained false. Private bodies and
worker streams were not exported or reacquired. The original 120-response run's
cause remains unknown: it did not retain the operation/error/framing details.

The downloaded 7,753-byte ZIP exactly matches GitHub's declared SHA256
`8969dbaab73528c82249fe4c6c54f968afb69bc9e3f9f0dae29af341738047e7`.
It contains only three bounded public JSON records. Independent734 accepted the
current protocol, full exact-integer source map equality, owned cleanup and
caught operation; it did not accept response text, dependency trust, native or
ordinary-consumer behavior, or issue closure. Two independently stable named-vs-
descriptor ctime differences and the reviewer's first overstrict passive refusal
are preserved without actor or cause inference.

The next owning patch must keep deadlines, byte caps, real EOF and framing
verification. A closed response must not trigger another timeout operation on
its released transport. Truncated responses and genuine open-socket errors must
remain refused. Only new/changed regressions and a changed one-request hosted
verification should precede any broader observation. #64 and #40 remain open.
No packages, release, deployment or Pages publication is authorized by this result.
