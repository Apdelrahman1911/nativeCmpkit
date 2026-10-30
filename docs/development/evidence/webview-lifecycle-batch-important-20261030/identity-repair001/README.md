# Owning native identity repair and failure-only WebKit recovery

The actual [first native batch](../native-ci002/README.md) remains failed:
four genuine UIKit-host methods pass; six actual document-readiness methods fail.
The original generic predicates do not identify their exact cause.

## Small owning change

`WebView.ios.kt` used Kotlin wrapper `===`/`!==` for native KVO, navigation-delegate,
load/evaluation and release ownership. Objective-C identity must instead compare
the retained native object's address during the owning call. The internal
`NativeWebViewIdentity.ios.kt` helper rejects null/null and different native views;
it neither uses value equality nor retains/exports addresses. All public signatures,
packages/framework names, native configuration and cleanup stages stay unchanged.

One new actual-UIKit method retrieves the mounted WKWebView through its native
parent's Objective-C collection, checks controlled KVO/delegate inputs for that
owner, and rejects foreign/null views. It explicitly does **not** substitute
delegate injection for a successful page load. The original six methods still
require actual native and observed titles, loading completion and owning-window
identity under the original **ten-second** timeout. Failure diagnostics now report
only bounded test-controlled titles/native booleans/progress/error codes, retaining
the original exception. Causality of the first six timeouts is **unverified**.

## Important tests and exact recovery

One owning lexical guard is first **red1/1**. The first expanded owning run remains
**FAILED22:21pass/one stale six-versus-seven fixture count**. Correcting that count
does not weaken native readiness or outcome requirements. The shared important
run passes **146/146 Python methods**, zero failures/errors/skips,5.694s, with all
**975 selected inputs held**. These are overlapping synthetic/lexical controller
methods, not Apple compilation or native executions. Actionlint1.7.12 and
whitespace checks pass. **Zero local Gradle/KLIB/link/native executions.**

Finite `ios-webview-recovery` requests exactly **seven** native methods: six failed
original WebKit cases plus the one new bridge boundary. The four accepted unchanged
host methods are not replayed; their helper/test bytes match16c9a530. The original
ten-method profile remains; unfiltered WebView now requires all eleven owning
methods, and all eleven platform slots remain. Actual Worker/runtime/binary/install/
cleanup and fresh nonzero XML gates remain mandatory. No source-only issue closure.

Single agent, maximum two combined heavy hosted requests, eight-GiB local reserve;
no publication, releases, deployment/Pages, main/history rewrite or independent
release/security gate changes.
