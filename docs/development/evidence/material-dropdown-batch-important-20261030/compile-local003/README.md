# Actual dropdown test compile recovery

`./gradlew :calf-ui:compileTestKotlinDesktop --max-workers=1
--no-configuration-cache --no-daemon` with the recorded JDK/compiler bounds exits0
after134.03s. **Zero executed tests**; compile success does not verify input,
pixels, dismissal, other platforms or release readiness.

The test-only dependency is
`org.jetbrains.androidx.navigationevent:navigationevent-compose:1.1.0`, the exact
existing UI1.12 runtime dependency. All917 library/994 combined dirty-snapshot
inputs are held. The affected back-route source guard passes; failed compilation
and the actual first runtime diagnostic are retained. The immutable four-target
dropdown request is still required. #132 remains open.
