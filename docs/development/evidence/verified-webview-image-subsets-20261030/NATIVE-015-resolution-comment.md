<!-- nativecmpkit-resolution:NATIVE-015:focused-verified-subset:20261030:81ff78b5 -->
## Verified resolution — focused shared batch, verified subset only

1. Actual engine string, number, object, JSON null, undefined and throwing scripts pass in Android Chromium (41003730413), iOS WebKit (40997536117), JavaFX and Chrome JS/Wasm (40999700359). The additive typed API uses a JSON envelope; the legacy native-format API remains available.

2. Each engine fixture evaluates before attach, after disposal, disabled and with invocation-local callbacks. Actual Android instrumentation/iOS owned Worker/desktop worker invoke off the native UI thread and assert main/FX delivery; browser is single-threaded. Current navigator/lifecycle callbacks are separately reviewed in accepted replacement methods; no shared mutable evaluator callback is retained.

3. Real JavaFX/browser throwing callbacks escape once and do not become script errors; Android detached actual callback plus eight exact unchanged native-fault host methods verify synchronous/asynchronous callback/native exceptions, duplicate suppression and post-release delivery. iOS detached main callback escapes once; attached asynchronous app callbacks must not throw across Objective-C. This is not a guarantee of delivery when native destruction drops an already-pending callback, explicitly documented.

Actual fresh Android value case: immutable `81ff78b56ddefe1452bea41c51e6d7123dfa37ed`, [run41003730413](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41003730413), one passed value method within **FAILED2-case connected suite** (Gradle exit1/78.03s), no errors/skips, actual provider/runtime and all904 before/after exact Git inputs. Controller ownership/Enforcing API35/clean shutdown0 reviewed. Other engine value methods and eight unchanged host fault regressions are reused, not rerun or represented as new tests. Current decoder/evaluator/dispatch source is bound; later iOS change adds final child detachment only, not evaluator changes.

Limitations and still-open related work:
- Native platform may drop an already-pending callback on destruction; no delivery/Promise-await guarantee beyond the documented start/completion contract.
- iOS asynchronous application callbacks must not throw across Objective-C; detached exception behavior is verified without crashing the native test host.
- Actual Enforcing API35 emulator, current iOS simulator, Linux JavaFX and Chrome JS/Wasm only; no physical/minimum-provider/macOS/Windows/other-browser or ABI/consumer/security/release certification.
- #62/#89 remount issues remain open; shared41003730413 remains FAILED (Android remount failure/iOS zero-execution compiler error).

Original technical body, labels, attribution and history remain unchanged. Readback and exact acceptance receipts are archived afterward under `docs/development/evidence/verified-webview-image-subsets-important-20261030/`. No packages/releases/deployments/Pages or main/history changes.
