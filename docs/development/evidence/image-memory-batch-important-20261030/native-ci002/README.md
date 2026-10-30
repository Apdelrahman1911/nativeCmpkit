# Actual strict Apple image-memory recovery: startup abort, zero tests

[40989310808](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40989310808)
at `35b266c88fc243ca672cebad1dd31d34eebb423c` **FAILED**. The actual compiler and
application linker now succeed, but Gradle exits **1 / 1361.63 s**. There are
**zero XML reports and zero executed pixel, GC, allocation or leak methods**.
All **890** exact historical Git library inputs match before/after. See
[independent review](review.json) and [source analysis](startup-source-analysis.json).

The installed, signed-byte-verified application aborts before UIApplication
activation at Kotlin/Native `ObjCInterop.mm:278`: **Unable to add protocol to
Objective-C class**. The stack includes `CreateKotlinObjCClass` and Compose's
eager `Accessibility.ios.kt` initializer. This test-only binary requested
`runtimeAssertionsMode=panic` and `checkStateAtExternalCalls=true`; the exact
offending class/protocol is **not identified**. Redundant/inherited conformance
is a hypothesis, not an executed diagnosis or a confirmed production crash.
Previous successful default-mode binaries do not certify this strict mode.

Actual PID **68364**, transport **11.64 s**, console exit **0**, but activation,
Worker and completion are missing: the transport correctly fails
`missing-activation`. Owned application cleanup succeeds. No matching owned
crash report was found; that is not proof of crash absence.

The profiler was prepared/cleaned but **never started**: `commands=[]`,
`exports=[]`, `profile_passed=false`. Neither an empty export nor successful
installation is an Instruments/ASan/leak/GC pass. **#140/UI-037 and #141/UI-038
remain open.** Nine accepted unchanged UIImage methods are reused, not replayed.
Do not rerun this unchanged strict profile, silently remove its assertions, or
claim an alternate profile satisfies the original criteria without explicit
source-bound tool/runtime evidence. No release, package, Pages, main/history or
independent security gate changes.
