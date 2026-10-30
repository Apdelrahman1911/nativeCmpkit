# Navigation/geo public contract batch — #96/#115

The two modules intentionally remain unpublished experiments. A standalone
[common and Android source consumer](../../tests/consumer/navigation-geo-source/README.md)
uses two explicit composite substitutions, both adaptive factories/public host,
the distinct legacy platform bridge and the common geo factory/result/snapshot/
no-fix/close contract. It does not declare hidden AndroidX/GMS dependencies.

Actual held Android compiler output confirms two library defects: the public
AndroidX controller typealias/receiver and LocationTracker Google superclass
were hidden by implementation dependencies. The owning repair exposes the existing
dependencies through api, including public Lifecycle/FragmentManager signatures.
No versions, packages, superclass, method descriptors or target minimums change.

One genuine library-level Android BACK method exercises public factory identity,
duplicate visits/saveable state, one-event pop, replacement and handler disposal/
application fallback with real native input. Completed system back is supported;
predictive gesture progress/animation is not. Application-provided popBackStack
works as an independent Compose action; UIKit native/interactive stacks, browser
history, desktop shortcuts and per-entry ViewModel/lifecycle owners remain
unsupported. Saveable per-entry state has its existing documented contract.

[Implementation/source-red/important tooling](evidence/navigation-geo-public-contracts-20261030/implementation001/README.md)
records101 synthetic accepted methods, not native/compiler success. #96/#115
remain open pending immutable six-target source compilation, exact applicability
review of already accepted unchanged nav/geo runtimes, native1-case result and
all original criteria. There is no reason to repeat accepted runtime methods.

Non-Android acquisition returns Unsupported, not browser GPS or CoreLocation
privacy/watch behavior. Android source/host injection is not live GMS/GPS/device
permission evidence. No packages/ABI/physical/minimum/dependency/legal/security/
release gate is inferred; no publication/release/deployment/Pages/main/history.
