## Verified fix — direct closure after important actual rendering tests

Both **original UI-044 acceptance criteria** pass at immutable **fe75ac86da6bb22f6c02a7fcadf8334184b10b7f**. The focused Linux/Xvfb command executes **7/7 actual library methods**, two fresh XML, zero failures/errors/skips, exit0/44.01seconds. **4/4 are the indicator methods**; these are part of the7, not additional executions. No unrelated suite is replayed.

- Real production Canvas/Skia pixels: transparent color paints nothing; every half-alpha frame stays within the input opacity; the first inactive spoke has the same single-paint alpha as its matching peer, not a ninth coincident stroke.
- A new **actual public CupertinoActivityIndicator composition** drives its real one-second infinite transition with a controlled clock. All eight frames plus the restart are compared pixel-for-pixel against the production painter on white:80×80 RGBA,2/255 tolerance, zero differing pixels. Indeterminate progress semantics remains at every frame and after a dynamic transparent-color update. The transparent update leaves the whole snapshot white, not a cached opaque spinner.

Owning production repair: exactly eight unique angles, input alpha multiplied by per-spoke intensity. Existing public API, one-second transition and progress semantics are retained. That implementation predates this continuation; the new change here is the substantive public-composition regression and verified acceptance.

Review checks745 exact own-Git inputs, before/after source equality, all seven original authored testcase identities with the exact desktop target marker, two fresh XML and actual Gradle9.7.1/JDK17.0.20(Ubuntu)/Linux runtime. Offline dependency and initial fixture-compilation failures remain failures with **zero executed tests**; preexisting XML was stale and never counted.

Important tests → source/results review → **direct closure now** → archive/index afterward. Evidence will be retained under `docs/development/evidence/ui-important-20261028/online002/`. Original issue body/title/labels preserved.

This is actual Compose/Skia rendering on Linux, not UIKit UIActivityIndicator, another OS/branch, assistive-device/native-touch or full release/security/consumer/ABI/dependency/legal certification. Nothing published or deployed.

<!-- nativecmpkit:direct-acceptance:UI-044:fe75ac86 -->
