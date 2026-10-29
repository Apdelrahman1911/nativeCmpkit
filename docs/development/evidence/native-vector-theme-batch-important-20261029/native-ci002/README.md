# Shared native test-fixture compile failure

Run [40897045067](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40897045067) at immutable `1bdc61f8e5867069d6410b2ca7f8af91f2e1bbc5` is **FAILED**.
Linux tooling passes, but native Gradle exits1 after 890.31s
at `compileTestKotlinIosSimulatorArm64`; **zero selected application task markers,
zero native executions/XML/application receipts**. 5 selected methods were not executed.
All873 before/after inputs match exact historical Git; actual plan/command/runtime,
workflow and artifact digest are independently reviewed.

The owning compiler diagnostic is `calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/NativeVectorThemeAcceptanceTest.kt:229:24`,
`'val' cannot be reassigned.` Kotlin/UIKit exposes the inherited preferredContentSize
getter as val and UIViewController supplies the explicit setter method. Both focused
runs share this same unexecuted fixture blocker. This failure is preserved before
repair, not transformed into a passing test, memory/Worker/cleanup or release claim.
Prior completed component/enable methods are reused explicitly, not replayed.

Issues #34/#137/#139/#143 remain open. No publishing/releases/deployments/Pages,
main/history changes or independent release/security gate waiver.
