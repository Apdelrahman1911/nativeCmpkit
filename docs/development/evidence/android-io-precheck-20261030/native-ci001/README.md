# Actual Android known-size refusal — verified narrowly

[Run41096681326](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41096681326),
attempt1 at `c54d02836347f35b1caa8cb22a2038119fbbc41d`, **succeeds**:
API35 **1/1 actual native method / one fresh XML**, Gradle0/47.02s.
`KmpFileDeviceTest.knownOversizeIsRejectedBeforeAnyNativeStreamIsOpened`
reads real provider metadata64, refuses bounded63 and asserts **zero provider
opens/descriptors**.987 library/1064 combined inputs match exact Git; Enforcing
runtime, fresh marker/filter/report and owned graceful emulator exit reviewed.

The first independent reviewer erroneously required a camera-only ADB-transport
field; its failure is preserved. The corrected reviewer retains the real normal
IO profile's graceful child exit/no force. **Separate ADB-transport removal
readback is unavailable**, not inferred. Earlier null-size/provider-death failure
remains unexplained; no retrospective MIME or lifecycle diagnosis is invented.

This clears the standalone native precheck gap only, not all #45/#55/#57 criteria,
Coil decoder/cancellation/provider/key/memory matrices or physical/minimum/platform,
packaged/API-ABI/legal/dependency/security/release gates. No accepted unrelated
suite replay, new library change, publishing, Pages/main/history or issue closure.
