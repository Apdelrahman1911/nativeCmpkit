# Windows/Linux ARM64 original security results and failed-only TLS recovery

## Original native run — retain FAILED

[41542403515](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41542403515)
at `635202b7336429b821ef85e9261f42f5838a6a23` executed only the remaining
Windows3/Linux ARM644 methods. Originals were acquired **once**; no archive is
redownloaded. [REVIEW407](407/REVIEW407.json) accepts 66 passive source/results/
graph checks and all **1,219** actual before/after input maps against frozen Git.

| Host | Native results | Original XML | Gradle |
|---|---|---:|---|
| Linux ARM64 | TLS/rendering, cookie, JavaScript policy, media **4/4** | 4 | 0 /103.02s |
| Windows x64 | Cookie/policy **2/2**; TLS **failed** | 3 | 1 /97.11s |

**Accept and exclude those six passing methods from unchanged replay.** The
original Windows all-green worker parser correctly remains red. Both full host
graphs (24 runtime +48 compile/test configurations each) qualify at 1,222 held
graph inputs, including the workflow and two collectors. Each has six aligned
JavaFX21.0.13 native classifiers. Do not reacquire these graphs. Reuse the
[macOS policies](../desktop-policy-native402-404/README.md), macOS TLS/cookie
and earlier Linux/navigation/media evidence on their applicable unchanged bytes.

## C1 advisory delta — four queries only

[ADVISORY408](408/ADVISORY408.json) records one HTTP200 response to four genuinely
new exact Compose Desktop1.12.0/Skiko0.150.1 host coordinates: **four results,
zero coordinate matches,1.029912s**. Linux142 and macOS4 prior observations are
reused; the union covers **150** unique coordinates across all five desktop
hosts. No embedded-engine exploit, independent byte trust, licensing, consumer,
API–ABI or release clearance is inferred from zero OSV matches.

## Confirmed Windows fixture defect and owning correction

The TLS method fails before its original native rejection assertions:
`Owned TLS fixture failed: endpoint=untrusted phase=Handshake`. The cause is
`SocketException: An established connection was aborted by the software in your
host machine`, at the actual Java17 TLS1.3 Finished-write eight-frame prefix,
followed by the owning `SSLSocketImpl.startHandshake`/`Endpoint.respond` caller.
The previously narrow classifier recognizes only `Broken pipe` and therefore
mistakes this observed Windows Finished-write termination for an immediate
fatal fixture error. Historical native certificate rejection is **not** claimed.

The internal test-only `observedDesktopTlsFinishedWrite` now admits that exact
class/message/Java17/stack shape **only on Windows**, retaining the earlier
Broken-pipe behavior. Trusted, post-handshake, non-handshake, closing, wrong
version/class/message/unowned-stack errors stay fatal. Recognized failures stay
**pending** until all unchanged native SSL/error/zero-HTTP predicates confirm
rejection; cleanup and pending-observation failures remain strict. No permissive
trust manager, TLS waiver, production API or dependency version change exists.
The original native TLS source remains byte-identical
(`00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c`).

[QUALIFICATION409](409/QUALIFICATION409.json): **8 NEW +3 affected historical
controls =11/11**,1.944s;20 passive owning checks/Actionlint0. Exact six bindings/
11 reversible fragments compose before the unchanged seven18-fragment policy
manifest; old pins are not refreshed and historical images cannot substitute
for current native sources. The only live workflow change adds one choice.

[KOTLIN410](410/KOTLIN410.json): fresh actual library JVM classifier regressions
**3/3**,one original XML/Gradle0/111.50s/JDK17.0.20/Gradle9.7.1/all1,223 inputs
held; production compile UP-TO-DATE and edited test compiler genuinely executed.
These are synthetic-stack classifier tests: **ZERO new native TLS outcomes**.
Only seven owning test/tooling inputs changed and four were added;1,212 prior
library inputs remain exact. No accepted suite or native method was replayed.

## Next execution and closure rule

Only `webview-desktop-tls-windows-recovery` may run: Windows x64, original TLS
method1/XML1, no cookie/policy/media or graph capture. Commit/push development
only, reconcile hosted capacity and freeze source first. If that method passes,
review all three literal #144/BUILD-002 criteria and close immediately, before
further documentation. #64 ordinary candidate adoption/corresponding-source/
legal/security/consumer/API–ABI remains separate.

Totals unchanged: **97 closed /75 open /172**; ledger **22 implemented /42
partial /95 verified /5 unresolved**. Solo/serial local-heavy/8GiB reserve/max2
hosted-heavy including queued, read-only Actions/all/no mandatory SHA pinning.
No release/package/deployment, Pages/main/history change or readiness/security
waiver. [Archive inventory](archived-files410.json) binds every public payload.
