# Shared UIImage memory/ownership batch — candidate, not native verification

Owning issues **#140/UI-037 and #141/UI-038 remain open**. No source/API rewrite:
existing explicit premultiplied sRGB RGBA conversion, CoreGraphics-owned copy and
nested release ownership are exercised by **three new library-level native cases**.
Nine previously accepted UIImage methods are reused, not replayed.

1. One real1MP image (4MiB pixel buffer), a separately owned GC Worker gated at
   the real context→snapshot boundary, three concurrent collections/6MiB controlled
   pressure, original Skia fixture closure, five further collections, actual sRGB
   name/dimensions/scale and every native RGBA byte. Future results are consumed once;
   original Worker exceptions, bounded termination and independent fixture cleanup stay.
2. Eight rounds of all nine null/exception native failure boundaries plus success
   (80 conversions), actual allocations/releases, GC, sRGB and actual native pixels.
3. Bounded real library conversion/failure workload in the exact owned UIKit app/PID
   while an actual Instruments/leaks attempt runs. No sample application stand-in.
   Native process observes Darwin heap requests; unique private ack proves **attempt
   completion only**, not profiler support. Private traces/addresses/heap/logs/binaries
   never upload. Missing schemas, unrelated frames, nonzero/missing/foreign leak
   summaries or cleanup uncertainty cannot certify the profile.

Only `ios-image-memory` selects these new methods on one Apple host. Existing
11 full slots and application/XML/Worker/runtime/binary/install/owned-cleanup
gates remain; opt-in runtime assertions affect only its test executable, not
public frameworks. [Configured compiler review](native-options001/README.md)
explains unsupported sanitizer settings precisely, not an executed ASan claim.

[Owning fixture recovery](important001/owning-recovery001.json) **99/99** synthetic
methods/all967 selected sample/library/build/tool inputs held. First five-guard
red and the entire881-method run's **12failure/7error events** remain failed in
[original receipts](important001/shared-ci001.json): new full-host/profile fixtures
were missing/stale, not evidence of a library/native failure. Only affected
fixtures recovered; the881 methods are not replayed locally. After the final
Worker-exception preservation refinement, [seven memory guards](important001/final-owning001.json)
pass7/7 with the only subsequent source change explicitly named. These counts
overlap, not106 unique methods. Actionlint1.7.12, whitespace and resolution-index
checks pass. **Zero local Gradle/KLIB/link/UIKit/library executions** below8GiB.

Immutable hosted verification and every original issue criterion are still
required. Close the reviewed verified subset together immediately; an unsupported
profile must not hold an independently verified UI-037 forever or falsely close
UI-038. No publishing, Pages, main/history, physical/minimum/ABI/consumer/security
or other independent release-gate change.
