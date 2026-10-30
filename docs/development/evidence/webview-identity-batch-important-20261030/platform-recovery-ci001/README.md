# Actual shared recovery: Desktop accepted, mobile remount still incomplete

[Run41003730413](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41003730413)
at `81ff78b56ddefe1452bea41c51e6d7123dfa37ed` remains **FAILED**. The
[independent review](review.json) checks904 library/981 combined exact historical
inputs, actual runtime/commands, fresh XML and separate owning lifecycle receipts.

- Desktop:1/1 actual public Compose/JavaFX creation/replacement/retained-remount
  method passes, Gradle0/269.09s.
- Android Enforcing API35/x86_64:2 executed/1 passed/1 failed, Gradle1/78.03s.
  Typed values/off-main/detached callback passes. Creation/remount fails after
  retained remount:expected `Value(json="owner-b")`, actual empty title at
  `awaitDocument` line164, caller105. Native/emulator ownership and clean shutdown0
  are verified; initial creation/replacement assertions reached.
- iOS:Gradle1/740.52s, **zero tests/XML/native application**. Exact compiler error
  at `IosWebViewLifecycleAcceptanceTest.kt:109:76`:actual `Any?`, expected
  `NSObject?` in the newly added retained-parent child assertion. No native
  cleanup/remount success is inferred.

Three actual executions/two accepted, not four passes. Prior accepted engine
methods are not replayed. #72's independent original-criteria closure does not
close #62/#89 or satisfy network/error/swipe/video, minimum/platform, ABI/consumer/
security/release gates. Preserve the failed archive and review mobile-only recovery.

