# Camera #13 — owning Settings UI lease

The actual [camera010 failure](../android-camera-provider-20261030/restoration-ci010/README.md)
remains failed: unavailable reflected `TRANSACTION_setAlwaysFinish`, before
service mutation/caller launch; absent-versus-hidden cause is unknown.

This **test-only** repair removes reflection/guessed transactions and uses the
installed public Developer Settings preference, supplied with real UiAutomation.
The Developer Options master must already equal **1**; it is never toggled.
Exact native/scalar/UI agreement remains mandatory. Original null/0/1 state,
accessibility flags and nonce-owned Settings task are restored with readback;
unknown/foreign/partial state or failed cleanup refuses success.

The original native AMS parser, production camera API, public TakePicture
launcher/registry/Android grants and all four native criteria remain intact.
Only the already-failed Dont-keep method is selected; three accepted restoration
methods are not replayed. The merged controller's exact three-hunk inverse retains
the complete browser/IO additions (`integration.json`).

**35 distinct important source/models pass** on the frozen candidate, reused
without replay; these are not Android execution. The merged required-source guard
and source-only plan pass. [Reporter compilation](../camera-browser-settings-compile-20261031/README.md)
passes **0 / 103.03 s** in the shared three-task invocation, not three builds.
Installed resources/tasks/master state and shell completion remain unobserved.

Preserve all prior native failures, source reds and private setup/parser refusals.
Pinned Android15 source identities and exact candidate/accepted-source
correspondence are archived. Normal Settings onStart can reassert master1 and run
its controllers; this is not a claim of zero internal writes/framework effects.

**#13 remains open.** A genuine Dont-keep execution and caller recreation while
the external recipient is still foreground are still required. Explicit
Activity.recreate or recreation observed only after return cannot substitute.
No minimum/physical/heap/consumer/ABI/security/release or publishing gate changes.
