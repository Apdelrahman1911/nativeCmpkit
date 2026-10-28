# Important controlled switch acceptance — 2026-10-28

UI-030/#134 remains open pending actual native execution and original criteria review.
Three new public UIKit/Compose methods check delayed owner acceptance against measured
thumb/semantics; thumb and both empty track ends, actual measured threshold crossing
and return without committing; disabled visual and semantics consistency. No production
or public API changes. Prior accepted control methods are not replayed.

Local focused tooling **4/4**, owning workflow/matrix **45/45**; these are synthetic
selection/receipt guards, not native tests. Actual simulator production/test KLIB
compile **0/47.01 s**, **820 held inputs**, JDK17: **zero native runtime tests**.
Finite `ios-switch-ownership` selects exactly three methods on the existing genuine
UIKit application, preserving strict XML, protocol, Worker and owned cleanup checks.
An immutable CI run is required; no device/assistive/minimum-OS/heap/ABI/consumer/
security/release certificate or publication/deployment is inferred.
