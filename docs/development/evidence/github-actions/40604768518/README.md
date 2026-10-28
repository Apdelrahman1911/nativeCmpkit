# Important Android stream ownership — 2026-10-27

[Run40604768518](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40604768518)
at `f37bf1416546ffe04bd1ec16707241cf662581b9` is **failed**:30/32 executions,
eight fresh XML, zero skips. IO27/27; Coil3/5. The entire suite is not green.

[Source/result review](important-result-review.json) accepts **all five original
IO-020 criteria** in six complete important methods: partial bytes/close1/suppressed
close; successful nonempty/empty close1; throwing close propagation; attached real
Android resolver/provider-null public call/FNF; actual production Coil failed fetch
after stream open with close1/actual FD invalid/read IOException/source intact.
Controlled Robolectric resolver transport is not Android device/provider Binder.
Additional complete Coil byte parity and decoder-cancellation ownership pass.

[#56 direct closure/readback](direct-closure/closure-readback.json) follows the
important review **before documentation**. Original body/title/labels retained;
**25 closed issues total**. All738 exact Git inputs, before/after maps, artifact
and XML hashes, fresh commands/runtime/SDK correspondence were reviewed, not
substituted by compilation. Later changed cache/Coil fixture source is not this run.

Two extra Coil tests fail **before final descriptor assertions**, hence no cleanup
pass claimed: a provider `apply` resolves `context` to its initially-null receiver;
a suspended decoder exception has matching IOException class/message but a
different object. The fixture now explicitly attaches outer application/context
and requires the actual null-open count. Error assertions retain type/message and
exact injected origin in a bounded cause chain rather than disabling JVM stack
recovery. All existing FD/close/cancellation guards remain. These fixture repairs
need their own fresh **Coil-only** run; unchanged accepted IO27 is not rerun.

One accepted dispatch; raw archive reports/receipts only, not private job/Gradle
logs. Device/minimum/provider-grant/native/sanitizer, legal/dependency/full consumer/
API-ABI/security/release gates remain. No releases/packages/Pages/deployments.
