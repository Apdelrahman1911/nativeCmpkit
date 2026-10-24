# Complete ordered backlog

Generated from every audit finding plus actionable historical requests. See [roadmap strategy](README.md), [machine-readable tests/dependencies](backlog.json), and [finding detail](../audit/findings-index.md). State is the last synchronized observation, not a live tracker.

## 0. Migration remediation already verified

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 1 | **BUILD-003** — Any nonempty prebuilt native subdirectory suppresses every local native build | High | M | — | open | [#2](https://github.com/Apdelrahman1911/nativeCmpkit/issues/2) |
| 2 | **BUILD-008** — Release version input is embedded directly in executable shell scripts | Medium | S | — | closed | [#41](https://github.com/Apdelrahman1911/nativeCmpkit/issues/41) |
| 3 | **BUILD-009** — Pinned JetBrains-only daemon prevents use of installed JDK 17 and contradicts CI setup | Medium | S | — | closed | [#42](https://github.com/Apdelrahman1911/nativeCmpkit/issues/42) |
| 4 | **BUILD-011** — Release staging duplicates both native libraries into both desktop artifacts | Low | S | BUILD-003 | closed | [#146](https://github.com/Apdelrahman1911/nativeCmpkit/issues/146) |

## 1. Before a supported preview

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 5 | **BUILD-001** — Desktop WebView POM hard-codes the publisher OS in JavaFX dependencies | High | L | — | open | [#1](https://github.com/Apdelrahman1911/nativeCmpkit/issues/1) |
| 6 | **BUILD-006** — Verification pipeline does not gate platform behavior, consumer compatibility, or native correctness | High | XL | — | open | [#3](https://github.com/Apdelrahman1911/nativeCmpkit/issues/3) |
| 7 | **IO-001** — iOS byte-array reads can overrun native destination memory and mishandle empty files | High | S | — | open | [#4](https://github.com/Apdelrahman1911/nativeCmpkit/issues/4) |
| 8 | **IO-002** — Android saver loses pending content across recomposition and can report an empty export as success | High | M | — | open | [#5](https://github.com/Apdelrahman1911/nativeCmpkit/issues/5) |
| 9 | **IO-003** — Desktop composition disposal races raw JNI handles; cancelled creation can leak handles | High | L | — | open | [#6](https://github.com/Apdelrahman1911/nativeCmpkit/issues/6) |
| 10 | **IO-004** — Desktop save can delete its own source and does not reliably replace existing content | High | M | — | open | [#7](https://github.com/Apdelrahman1911/nativeCmpkit/issues/7) |
| 11 | **NATIVE-001** — Desktop stopLoading re-enqueues itself instead of cancelling WebEngine loading | High | S | — | open | [#9](https://github.com/Apdelrahman1911/nativeCmpkit/issues/9) |
| 12 | **NATIVE-002** — Android and Desktop WebViews retain live native views after composition disposal | High | M | — | open | [#10](https://github.com/Apdelrahman1911/nativeCmpkit/issues/10) |
| 13 | **NATIVE-010** — Enabling Web JavaScript removes all iframe isolation for inline HTML | High | M | — | open | [#11](https://github.com/Apdelrahman1911/nativeCmpkit/issues/11) |
| 14 | **NATIVE-013** — Desktop CookieManager overwrites JavaFX and application-global cookie handlers | High | M | — | open | [#12](https://github.com/Apdelrahman1911/nativeCmpkit/issues/12) |
| 15 | **NATIVE-019** — Android camera loses its output URI across Activity/process recreation | High | M | — | open | [#13](https://github.com/Apdelrahman1911/nativeCmpkit/issues/13) |
| 16 | **NATIVE-027** — Desktop share fallback opens arbitrary files/URLs instead of offering an explicit sharing fallback | High | M | — | open | [#14](https://github.com/Apdelrahman1911/nativeCmpkit/issues/14) |
| 17 | **NAV-001** — Adaptive navigation silently discards per-navigation arguments | High | L | — | open | [#15](https://github.com/Apdelrahman1911/nativeCmpkit/issues/15) |
| 18 | **NAV-002** — Route-keyed saved state aliases duplicate back-stack entries and incompletely fixes #542 | High | L | NAV-001 | open | [#16](https://github.com/Apdelrahman1911/nativeCmpkit/issues/16) |
| 19 | **NAV-009** — Embedded Cupertino font requires MIT notices in distributed artifacts; baseline notice gap partially repaired | High | M | — | open | [#17](https://github.com/Apdelrahman1911/nativeCmpkit/issues/17) |
| 20 | **PERM-011** — iOS calendar uses the iOS17 full-access API without availability gating or matching usage descriptions | High | M | — | open | [#22](https://github.com/Apdelrahman1911/nativeCmpkit/issues/22) |
| 21 | **PERM-018** — Android LocationTracker never updates its public location states | High | M | — | open | [#24](https://github.com/Apdelrahman1911/nativeCmpkit/issues/24) |
| 22 | **UI-001** — iOS date state and native calendars do not enforce the documented UTC-day/year-range contract | High | M | — | open | [#26](https://github.com/Apdelrahman1911/nativeCmpkit/issues/26) |
| 23 | **UI-002** — Native date conversion treats user-calendar components as Gregorian dates | High | M | — | open | [#27](https://github.com/Apdelrahman1911/nativeCmpkit/issues/27) |
| 24 | **UI-012** — Presented iOS alerts update their text but retain original action and text-field callbacks | High | M | — | open | [#28](https://github.com/Apdelrahman1911/nativeCmpkit/issues/28) |
| 25 | **UI-013** — iOS action sheets are presented without an iPad popover anchor | High | M | — | open | [#29](https://github.com/Apdelrahman1911/nativeCmpkit/issues/29) |
| 26 | **UI-014** — Alert dismissal during presentation is dropped and cleanup shares user-dismiss callbacks | High | L | — | open | [#30](https://github.com/Apdelrahman1911/nativeCmpkit/issues/30) |
| 27 | **UI-020** — Native bar measurement permanently stops after several stable frames | High | M | — | open | [#32](https://github.com/Apdelrahman1911/nativeCmpkit/issues/32) |
| 28 | **UI-021** — Native bars live outside the Compose layout/transition hierarchy | High | L | UI-020 | open | [#33](https://github.com/Apdelrahman1911/nativeCmpkit/issues/33) |
| 29 | **UI-027** — Liquid Glass slider retains stale enabled, range, geometry and direction inside drag callbacks | High | M | — | open | [#34](https://github.com/Apdelrahman1911/nativeCmpkit/issues/34) |
| 30 | **UI-040** — calf-ui test coverage omits all native managers and most interactive control families | High | L | — | open | [#37](https://github.com/Apdelrahman1911/nativeCmpkit/issues/37) |
| 31 | **BUILD-004** — Packaged native platform matrix omits Linux arm64 and Windows arm64 paths expected by loaders | Medium | L | BUILD-003 | open | [#38](https://github.com/Apdelrahman1911/nativeCmpkit/issues/38) |
| 32 | **BUILD-005** — Native release binaries have unlocked Rust dependencies and a floating compiler | Medium | M | — | open | [#39](https://github.com/Apdelrahman1911/nativeCmpkit/issues/39) |
| 33 | **BUILD-007** — Dependency and workflow trust is not reproducibly verified beyond the wrapper | Medium | L | — | open | [#40](https://github.com/Apdelrahman1911/nativeCmpkit/issues/40) |
| 34 | **IO-008** — Picked-file access lifetime is not represented for security-scoped folders or persisted Android URIs | Medium | L | — | open | [#45](https://github.com/Apdelrahman1911/nativeCmpkit/issues/45) |
| 35 | **IO-005** — iOS saver exports the original source with move semantics and ignores requested file names | High | M | IO-008 | open | [#8](https://github.com/Apdelrahman1911/nativeCmpkit/issues/8) |
| 36 | **PERM-001** — Android silently treats an unregistered Permission as granted | Medium | M | — | open | [#104](https://github.com/Apdelrahman1911/nativeCmpkit/issues/104) |
| 37 | **PERM-002** — Android bulk results are assigned to the first global permission alias, not the requested permissions | High | M | PERM-001 | open | [#18](https://github.com/Apdelrahman1911/nativeCmpkit/issues/18) |
| 38 | **PERM-003** — Android bulk/child permission requests do not consistently deliver completion callbacks | Medium | M | PERM-002 | open | [#105](https://github.com/Apdelrahman1911/nativeCmpkit/issues/105) |
| 39 | **PERM-004** — Android location requests do not orchestrate fine/coarse and foreground/background prerequisites | High | L | PERM-003 | open | [#19](https://github.com/Apdelrahman1911/nativeCmpkit/issues/19) |
| 40 | **PERM-005** — Remembered permission objects retain obsolete result callbacks after recomposition | Medium | S | — | open | [#106](https://github.com/Apdelrahman1911/nativeCmpkit/issues/106) |
| 41 | **PERM-007** — iOS result callbacks are not main-thread/disposal safe and run before status refresh | Medium | L | PERM-005 | open | [#108](https://github.com/Apdelrahman1911/nativeCmpkit/issues/108) |
| 42 | **PERM-009** — iOS BackgroundLocation cannot upgrade an existing WhenInUse grant to Always | High | M | PERM-007 | open | [#21](https://github.com/Apdelrahman1911/nativeCmpkit/issues/21) |
| 43 | **PERM-008** — iOS multi-permission launch is concurrent and returns singleton results rather than a complete batch | High | L | PERM-003, PERM-007, PERM-009 | open | [#20](https://github.com/Apdelrahman1911/nativeCmpkit/issues/20) |
| 44 | **PERM-013** — iOS Wi-Fi status observation publishes a Bonjour service and conflates timeout/cancellation with denial | High | L | PERM-007 | open | [#23](https://github.com/Apdelrahman1911/nativeCmpkit/issues/23) |
| 45 | **PERM-020** — Android LocationTracker rebinding has no ownership boundary or coroutine cleanup | Medium | M | PERM-018 | open | [#116](https://github.com/Apdelrahman1911/nativeCmpkit/issues/116) |
| 46 | **PERM-021** — Android LocationTracker suppresses missing-permission checks and ignores provider failures | High | L | PERM-018, PERM-020 | open | [#25](https://github.com/Apdelrahman1911/nativeCmpkit/issues/25) |
| 47 | **UI-016** — iOS sheet programmatic transitions bypass confirmValueChange and skipHiddenState | Medium | M | — | open | [#125](https://github.com/Apdelrahman1911/nativeCmpkit/issues/125) |
| 48 | **UI-017** — iOS sheet state never tracks partial detents or interactive dismissal and uses reversed detent order | Medium | M | UI-016 | open | [#126](https://github.com/Apdelrahman1911/nativeCmpkit/issues/126) |
| 49 | **UI-018** — Sheet operation cancellation and disposal can leave native presentation and retained owners behind | High | L | UI-016, UI-017 | open | [#31](https://github.com/Apdelrahman1911/nativeCmpkit/issues/31) |
| 50 | **UI-030** — Liquid Glass switch can visually diverge from its controlled checked value | Medium | M | — | open | [#134](https://github.com/Apdelrahman1911/nativeCmpkit/issues/134) |
| 51 | **UI-029** — Liquid Glass slider and switch lack actionable accessibility and keyboard semantics | High | M | UI-030 | open | [#35](https://github.com/Apdelrahman1911/nativeCmpkit/issues/35) |
| 52 | **UI-031** — Cancelled pointer gestures can commit a Liquid Glass switch toggle | High | M | UI-030 | open | [#36](https://github.com/Apdelrahman1911/nativeCmpkit/issues/36) |
| 53 | **BUILD-002** — Pinned JavaFX media 19 matches a published low-severity security advisory | Low | M | BUILD-001 | open | [#144](https://github.com/Apdelrahman1911/nativeCmpkit/issues/144) |
| 54 | **BUILD-010** — Desktop resource processing always invokes an untracked release-mode Cargo build | Low | M | BUILD-003, BUILD-005 | open | [#145](https://github.com/Apdelrahman1911/nativeCmpkit/issues/145) |
| 55 | **BUILD-012** — Resolved Linux picker graph contains three newly unmaintained D-Bus crates | Low | M | BUILD-005 | open | [#147](https://github.com/Apdelrahman1911/nativeCmpkit/issues/147) |

## 2. Compatibility, robustness and performance

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 56 | **IO-006** — Save write failures can report success or escape without a completion/error result | Medium | L | IO-002, IO-004, IO-005 | open | [#43](https://github.com/Apdelrahman1911/nativeCmpkit/issues/43) |
| 57 | **IO-007** — iOS picker completion is not exactly once and document swipe dismissal is not observed | Medium | M | — | open | [#44](https://github.com/Apdelrahman1911/nativeCmpkit/issues/44) |
| 58 | **IO-009** — Browser file reads treat DONE as success and do not cancel or propagate FileReader failures | Medium | M | — | open | [#46](https://github.com/Apdelrahman1911/nativeCmpkit/issues/46) |
| 59 | **IO-010** — File-kind queries misclassify extensionless browser files and nonexistent paths | Medium | S | — | open | [#47](https://github.com/Apdelrahman1911/nativeCmpkit/issues/47) |
| 60 | **IO-011** — Web saver accepts onResult but never calls it or exposes download-only capability | Medium | L | — | open | [#48](https://github.com/Apdelrahman1911/nativeCmpkit/issues/48) |
| 61 | **IO-012** — Immediate web Blob URL revocation can race the browser download | Medium | S | — | open | [#49](https://github.com/Apdelrahman1911/nativeCmpkit/issues/49) |
| 62 | **IO-013** — iOS picked-file copies have no ownership cleanup and are created before result limits are applied | Medium | L | IO-007, IO-008 | open | [#50](https://github.com/Apdelrahman1911/nativeCmpkit/issues/50) |
| 63 | **IO-014** — Portable path/name metadata exposes encoded or unreadable references instead of the readable file | Medium | M | IO-008 | open | [#51](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51) |
| 64 | **IO-015** — Desktop MIME filtering omits modern image formats and silently disables unknown custom filters | Medium | M | — | open | [#52](https://github.com/Apdelrahman1911/nativeCmpkit/issues/52) |
| 65 | **IO-017** — Some remembered launchers retain stale selection limits, image representation and parent windows | Medium | S | IO-003 | open | [#53](https://github.com/Apdelrahman1911/nativeCmpkit/issues/53) |
| 66 | **IO-018** — Multiple selection accepts invalid limits and differs across platform fallback paths | Medium | M | — | open | [#54](https://github.com/Apdelrahman1911/nativeCmpkit/issues/54) |
| 67 | **IO-019** — Android folder selections are wrapped using single-document metadata and stream-based existence | Medium | M | IO-008, IO-010 | open | [#55](https://github.com/Apdelrahman1911/nativeCmpkit/issues/55) |
| 68 | **IO-020** — Android whole-file read leaks its input stream if reading fails | Medium | S | — | open | [#56](https://github.com/Apdelrahman1911/nativeCmpkit/issues/56) |
| 69 | **IO-021** — Coil fetches eagerly copy whole files and the byte-array API needs explicit scheduling/size guidance | Medium | L | IO-001, IO-020 | open | [#57](https://github.com/Apdelrahman1911/nativeCmpkit/issues/57) |
| 70 | **IO-023** — Native parent-window pointers have unproven lifetime and thread-affinity guarantees | Medium | L | IO-003, IO-017 | open | [#58](https://github.com/Apdelrahman1911/nativeCmpkit/issues/58) |
| 71 | **IO-024** — JNI path conversion silently replaces non-Unicode filenames | Medium | M | IO-006 | open | [#59](https://github.com/Apdelrahman1911/nativeCmpkit/issues/59) |
| 72 | **IO-025** — iOS Document filter maps an application MIME wildcard to the application-bundle UTI | Medium | M | IO-015 | open | [#60](https://github.com/Apdelrahman1911/nativeCmpkit/issues/60) |
| 73 | **IO-026** — Web picker catches application callback failures as cancellation and lacks disposal cleanup | Medium | M | — | open | [#61](https://github.com/Apdelrahman1911/nativeCmpkit/issues/61) |
| 74 | **NATIVE-003** — Android and iOS onCreated run before the advertised native WebView reference exists | Medium | S | — | open | [#62](https://github.com/Apdelrahman1911/nativeCmpkit/issues/62) |
| 75 | **NATIVE-004** — Web state-driven URL loading does not clear existing iframe srcdoc | Medium | S | — | open | [#63](https://github.com/Apdelrahman1911/nativeCmpkit/issues/63) |
| 76 | **NATIVE-005** — WebView request state is not reset consistently on Desktop, iOS and Web | Medium | M | — | open | [#64](https://github.com/Apdelrahman1911/nativeCmpkit/issues/64) |
| 77 | **NATIVE-006** — Web WebView never invokes onDispose and retains iframe/listener references | Medium | M | — | open | [#65](https://github.com/Apdelrahman1911/nativeCmpkit/issues/65) |
| 78 | **NATIVE-007** — Non-Android saveable WebView state restores metadata but no content | Medium | M | — | open | [#66](https://github.com/Apdelrahman1911/nativeCmpkit/issues/66) |
| 79 | **NATIVE-008** — Replay-one navigation flow replays transient back/forward/stop commands on reattachment | Medium | M | — | open | [#67](https://github.com/Apdelrahman1911/nativeCmpkit/issues/67) |
| 80 | **NATIVE-009** — iOS captureBackPresses=false is overridden by settings and URL loads | Medium | S | — | open | [#68](https://github.com/Apdelrahman1911/nativeCmpkit/issues/68) |
| 81 | **NATIVE-011** — Browser CookieManager silently misrepresents URL, expiry, HttpOnly and deletion support | Medium | M | — | open | [#69](https://github.com/Apdelrahman1911/nativeCmpkit/issues/69) |
| 82 | **NATIVE-012** — Desktop and iOS getCookies do not implement full request-URL cookie matching | Medium | M | — | open | [#70](https://github.com/Apdelrahman1911/nativeCmpkit/issues/70) |
| 83 | **NATIVE-014** — Desktop cookie expiry is recalculated from read time and drifts into the future | Medium | S | — | open | [#71](https://github.com/Apdelrahman1911/nativeCmpkit/issues/71) |
| 84 | **NATIVE-015** — JavaScript evaluation has inconsistent failure, result and thread semantics | Medium | M | — | open | [#72](https://github.com/Apdelrahman1911/nativeCmpkit/issues/72) |
| 85 | **NATIVE-016** — Common WebContent options are silently ignored on several targets | Medium | M | — | open | [#73](https://github.com/Apdelrahman1911/nativeCmpkit/issues/73) |
| 86 | **NATIVE-017** — iOS inline-media configuration is changed only after WKWebView construction | Medium | M | — | open | [#74](https://github.com/Apdelrahman1911/nativeCmpkit/issues/74) |
| 87 | **NATIVE-018** — Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes | Medium | M | — | open | [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75) |
| 88 | **NATIVE-020** — Camera callback/lifetime handling is unstable across recomposition | Medium | M | — | open | [#76](https://github.com/Apdelrahman1911/nativeCmpkit/issues/76) |
| 89 | **NATIVE-021** — Camera API silently drops unsupported, cancelled and failed operations | Medium | M | — | open | [#77](https://github.com/Apdelrahman1911/nativeCmpkit/issues/77) |
| 90 | **NATIVE-022** — Android camera hardcodes a host FileProvider authority without public setup or validation | Medium | M | — | open | [#78](https://github.com/Apdelrahman1911/nativeCmpkit/issues/78) |
| 91 | **NATIVE-023** — iOS camera has no in-flight presentation guard or lifecycle-bound cleanup | Medium | M | NATIVE-020 | open | [#79](https://github.com/Apdelrahman1911/nativeCmpkit/issues/79) |
| 92 | **NATIVE-024** — Camera capture does synchronous full-resolution PNG work and has no temporary-file ownership policy | Medium | M | — | open | [#80](https://github.com/Apdelrahman1911/nativeCmpkit/issues/80) |
| 93 | **NATIVE-025** — ShareResult.Success means chooser launch/service selection rather than completed sharing on some targets | Medium | M | — | open | [#81](https://github.com/Apdelrahman1911/nativeCmpkit/issues/81) |
| 94 | **NATIVE-026** — Web clipboard fallback reports success before its promise resolves | Medium | S | — | open | [#82](https://github.com/Apdelrahman1911/nativeCmpkit/issues/82) |
| 95 | **NATIVE-028** — Android file sharing forwards file:// URIs without FileProvider conversion | Medium | M | — | open | [#83](https://github.com/Apdelrahman1911/nativeCmpkit/issues/83) |
| 96 | **NATIVE-029** — macOS share leaks both the Objective-C delegate and its Arc completion state on every presented picker | Medium | M | — | open | [#84](https://github.com/Apdelrahman1911/nativeCmpkit/issues/84) |
| 97 | **NATIVE-030** — macOS sharing blocks a coroutine worker for up to five minutes without cancellation integration | Medium | L | NATIVE-029 | open | [#85](https://github.com/Apdelrahman1911/nativeCmpkit/issues/85) |
| 98 | **NATIVE-031** — Desktop native share extraction uses one mutable filename across versions, architectures and processes | Medium | M | — | open | [#86](https://github.com/Apdelrahman1911/nativeCmpkit/issues/86) |
| 99 | **NATIVE-032** — Share callbacks can be delivered twice when application result handling throws | Medium | S | — | open | [#87](https://github.com/Apdelrahman1911/nativeCmpkit/issues/87) |
| 100 | **NATIVE-033** — Public mobile launch/evaluation operations lack an explicit main-thread contract or enforcement | Medium | M | — | open | [#88](https://github.com/Apdelrahman1911/nativeCmpkit/issues/88) |
| 101 | **NATIVE-037** — Replacing WebViewState or native lifecycle callbacks at the same composable identity is not safely rebound | Medium | M | NATIVE-002, NATIVE-006 | open | [#89](https://github.com/Apdelrahman1911/nativeCmpkit/issues/89) |
| 102 | **NATIVE-038** — Android enables multiple WebView windows but supplies no window-creation handler | Medium | M | — | open | [#90](https://github.com/Apdelrahman1911/nativeCmpkit/issues/90) |
| 103 | **NAV-003** — NavArgument builder rejects missing/null defaults and accepts mismatched typed defaults | Medium | M | — | open | [#91](https://github.com/Apdelrahman1911/nativeCmpkit/issues/91) |
| 104 | **NAV-004** — AdaptiveBundle violates documented runtime type and fallback contracts | Medium | M | — | open | [#92](https://github.com/Apdelrahman1911/nativeCmpkit/issues/92) |
| 105 | **NAV-005** — AdaptiveNavType inference and serialization are incomplete and not reliably round-trippable | Medium | M | NAV-003, NAV-004 | open | [#93](https://github.com/Apdelrahman1911/nativeCmpkit/issues/93) |
| 106 | **NAV-006** — AdaptiveNavHost retains stale graph closures and does not initialize a replacement controller | Medium | M | NAV-001, NAV-002 | open | [#94](https://github.com/Apdelrahman1911/nativeCmpkit/issues/94) |
| 107 | **NAV-007** — Unknown routes and duplicate graph registrations silently render blank or select the first definition | Medium | M | NAV-001 | open | [#95](https://github.com/Apdelrahman1911/nativeCmpkit/issues/95) |
| 108 | **NAV-008** — Navigation exposes two incompatible controller abstractions and lacks a declared platform capability contract | Medium | L | — | open | [#96](https://github.com/Apdelrahman1911/nativeCmpkit/issues/96) |
| 109 | **NAV-010** — CupertinoIcon leaves the private-use glyph Text semantics exposed | Medium | M | — | open | [#97](https://github.com/Apdelrahman1911/nativeCmpkit/issues/97) |
| 110 | **NAV-011** — Generated icon/symbol catalogues lack a reproducible generator and Apple availability metadata | Medium | M | NAV-009 | open | [#98](https://github.com/Apdelrahman1911/nativeCmpkit/issues/98) |
| 111 | **NAV-012** — Sample secure password text field logs every entered value | Medium | S | — | open | [#99](https://github.com/Apdelrahman1911/nativeCmpkit/issues/99) |
| 112 | **NAV-013** — Sample image export runs unbounded reads and image allocations without error or concurrency control | Medium | M | — | open | [#100](https://github.com/Apdelrahman1911/nativeCmpkit/issues/100) |
| 113 | **NAV-014** — Streaming sample cancellation does not interrupt its synchronous read loop | Medium | S | — | open | [#101](https://github.com/Apdelrahman1911/nativeCmpkit/issues/101) |
| 114 | **NAV-015** — Android sample permission menu and manifest disagree and declare unrelated broad permissions | Medium | S | — | open | [#102](https://github.com/Apdelrahman1911/nativeCmpkit/issues/102) |
| 115 | **NAV-018** — Derived Apache-2.0 source attribution needs reconstruction and artifact verification | Medium | M | NAV-008 | open | [#103](https://github.com/Apdelrahman1911/nativeCmpkit/issues/103) |
| 116 | **PERM-006** — Permission lifecycle refresh skips previously granted permissions, leaving revocations stale | Medium | M | PERM-013 | open | [#107](https://github.com/Apdelrahman1911/nativeCmpkit/issues/107) |
| 117 | **PERM-010** — iOS location delegates consume pending requests on nonterminal events and overwrite overlapping callbacks | Medium | M | PERM-007, PERM-009 | open | [#109](https://github.com/Apdelrahman1911/nativeCmpkit/issues/109) |
| 118 | **PERM-012** — iOS WriteCalendar requests full read/write access and rejects write-only authorization | Medium | M | PERM-011 | open | [#110](https://github.com/Apdelrahman1911/nativeCmpkit/issues/110) |
| 119 | **PERM-014** — iOS Bluetooth request lifetime and completion need device-backed hardening | Medium | M | PERM-007 | open | [#111](https://github.com/Apdelrahman1911/nativeCmpkit/issues/111) |
| 120 | **PERM-015** — iOS RemoteNotification skips APNs registration when notification authorization already exists | Medium | M | PERM-007 | open | [#112](https://github.com/Apdelrahman1911/nativeCmpkit/issues/112) |
| 121 | **PERM-016** — PermissionStatus loses partial capability, precision and requestability distinctions | Medium | L | — | open | [#113](https://github.com/Apdelrahman1911/nativeCmpkit/issues/113) |
| 122 | **PERM-017** — Desktop, JS and Wasm permissions are nonfunctional stubs with silent callbacks | Medium | L | PERM-016 | open | [#114](https://github.com/Apdelrahman1911/nativeCmpkit/issues/114) |
| 123 | **PERM-019** — Non-Android geolocation trackers only print messages and report fabricated zero coordinates | Medium | XL | PERM-018 | open | [#115](https://github.com/Apdelrahman1911/nativeCmpkit/issues/115) |
| 124 | **PERM-022** — Android geo data treats missing accuracy/speed/bearing/altitude as real zero measurements | Medium | M | PERM-018 | open | [#117](https://github.com/Apdelrahman1911/nativeCmpkit/issues/117) |
| 125 | **PERM-024** — Storage guidance asks for all-files access that WriteStorage never requests or verifies | Medium | S | — | open | [#118](https://github.com/Apdelrahman1911/nativeCmpkit/issues/118) |
| 126 | **UI-003** — Replacing iOS date state can skip initialization effects for the new native picker | Medium | S | — | open | [#119](https://github.com/Apdelrahman1911/nativeCmpkit/issues/119) |
| 127 | **UI-004** — Empty or reversed date-bound intersections reach native interval APIs without a defined policy | Medium | M | — | open | [#120](https://github.com/Apdelrahman1911/nativeCmpkit/issues/120) |
| 128 | **UI-006** — Compact Material date dialog can commit stale or newly forbidden scratch selections | Medium | M | — | open | [#121](https://github.com/Apdelrahman1911/nativeCmpkit/issues/121) |
| 129 | **UI-007** — Native range highlighting eagerly allocates every day of a selected range on the UI path | Medium | L | — | open | [#122](https://github.com/Apdelrahman1911/nativeCmpkit/issues/122) |
| 130 | **UI-009** — Time-state constructor checks the hour twice and never validates the minute on iOS | Medium | S | — | open | [#123](https://github.com/Apdelrahman1911/nativeCmpkit/issues/123) |
| 131 | **UI-010** — Remembered native time picker keeps writing to the original state after replacement | Medium | S | — | open | [#124](https://github.com/Apdelrahman1911/nativeCmpkit/issues/124) |
| 132 | **UI-019** — Changing the sheet confirmation callback recreates remembered sheet state | Medium | S | — | open | [#127](https://github.com/Apdelrahman1911/nativeCmpkit/issues/127) |
| 133 | **UI-022** — Clearing native navigation-bar items leaves the previous tabs visible | Medium | S | — | open | [#128](https://github.com/Apdelrahman1911/nativeCmpkit/issues/128) |
| 134 | **UI-023** — iOS toolbar does not implement its documented Material fallback | Medium | M | — | open | [#129](https://github.com/Apdelrahman1911/nativeCmpkit/issues/129) |
| 135 | **UI-024** — Dropdown availability check rejects later iOS major versions and selects a private-gesture fallback | Medium | S | — | open | [#130](https://github.com/Apdelrahman1911/nativeCmpkit/issues/130) |
| 136 | **UI-025** — Native dropdown reports dismissal immediately after opening and cannot follow expanded=false | Medium | M | UI-024 | open | [#131](https://github.com/Apdelrahman1911/nativeCmpkit/issues/131) |
| 137 | **UI-026** — Material dropdown silently drops most public popup and styling parameters | Medium | S | — | open | [#132](https://github.com/Apdelrahman1911/nativeCmpkit/issues/132) |
| 138 | **UI-032** — Liquid Glass slider arithmetic does not guard zero-length or invalid numeric ranges | Medium | M | — | open | [#135](https://github.com/Apdelrahman1911/nativeCmpkit/issues/135) |
| 139 | **UI-028** — AdaptiveSlider drops discrete steps on the iOS26 Liquid Glass branch | Medium | M | UI-029, UI-032 | open | [#133](https://github.com/Apdelrahman1911/nativeCmpkit/issues/133) |
| 140 | **UI-033** — Cupertino slider accessibility snapping fails for negative target values | Medium | S | — | open | [#136](https://github.com/Apdelrahman1911/nativeCmpkit/issues/136) |
| 141 | **UI-034** — Cupertino slider gesture state has incomplete keys and uncancelled competing tap animations | Medium | M | — | open | [#137](https://github.com/Apdelrahman1911/nativeCmpkit/issues/137) |
| 142 | **UI-035** — Several iOS adaptive visual and interaction parameters are accepted but unused | Medium | M | — | open | [#138](https://github.com/Apdelrahman1911/nativeCmpkit/issues/138) |
| 143 | **UI-036** — ImageVector-to-UIImage conversion discards vector paints, transforms and clipping | Medium | M | — | open | [#139](https://github.com/Apdelrahman1911/nativeCmpkit/issues/139) |
| 144 | **UI-037** — Bitmap-to-UIImage bridge has unverified byte-order, premultiplication and buffer-lifetime assumptions | Medium | M | — | open | [#140](https://github.com/Apdelrahman1911/nativeCmpkit/issues/140) |
| 145 | **UI-038** — Native image conversion leaks CoreGraphics resources on the image-creation failure path | Medium | S | UI-037 | open | [#141](https://github.com/Apdelrahman1911/nativeCmpkit/issues/141) |
| 146 | **UI-042** — Damped drag animation launches overlapping jobs per update and tracks velocity with wall-clock time | Medium | M | UI-031, UI-032 | open | [#142](https://github.com/Apdelrahman1911/nativeCmpkit/issues/142) |
| 147 | **UI-045** — Applying a native view theme also mutates its parent view style | Medium | M | — | open | [#143](https://github.com/Apdelrahman1911/nativeCmpkit/issues/143) |
| 168 | **Upstream #34** — [Medium][Upstream #34] Camera issue in webview iOS | Medium | triage-first | — | open | [#168](https://github.com/Apdelrahman1911/nativeCmpkit/issues/168) |

## 3. Breadth, polish and longer-term design

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 148 | **IO-016** — MIME lookup is locale-sensitive, parses only comma-space lists, and allocates per entry | Low | S | — | open | [#148](https://github.com/Apdelrahman1911/nativeCmpkit/issues/148) |
| 149 | **IO-022** — Native cache fallback can lose user isolation and loader trusts external search paths | Low | M | — | open | [#149](https://github.com/Apdelrahman1911/nativeCmpkit/issues/149) |
| 150 | **NATIVE-034** — Share subject is not delivered consistently and iOS assigns controller title instead of item subject | Low | M | — | open | [#150](https://github.com/Apdelrahman1911/nativeCmpkit/issues/150) |
| 151 | **NATIVE-035** — Maps, media and notification scaffolds must not be represented as implemented features | Low | L | — | open | [#151](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151) |
| 152 | **NATIVE-036** — Desktop customUserAgent cannot be reset to its documented default using null | Low | S | — | open | [#152](https://github.com/Apdelrahman1911/nativeCmpkit/issues/152) |
| 153 | **NATIVE-039** — WebView settings changes and error accumulation perform avoidable full updates | Low | M | — | open | [#153](https://github.com/Apdelrahman1911/nativeCmpkit/issues/153) |
| 154 | **NAV-016** — Sample includes an unused second navigation library with an unnecessary compatibility burden | Low | S | NAV-008 | open | [#154](https://github.com/Apdelrahman1911/nativeCmpkit/issues/154) |
| 155 | **NAV-017** — Showcase reports a successful clipboard action that it never performs | Low | S | — | open | [#155](https://github.com/Apdelrahman1911/nativeCmpkit/issues/155) |
| 156 | **PERM-023** — Specify and test the numerical domain and undefined-bearing policy of LatLng | Low | S | — | open | [#156](https://github.com/Apdelrahman1911/nativeCmpkit/issues/156) |
| 157 | **UI-005** — Single-date state loses displayed-month intent on iOS and save/restore | Low | M | — | open | [#157](https://github.com/Apdelrahman1911/nativeCmpkit/issues/157) |
| 158 | **UI-008** — No-selectable-day fallback is intentional but requires an explicit caller-visible validation policy | Low | S | — | open | [#158](https://github.com/Apdelrahman1911/nativeCmpkit/issues/158) |
| 159 | **UI-011** — Native time picker ignores the public is24Hour preference | Low | S | — | open | [#159](https://github.com/Apdelrahman1911/nativeCmpkit/issues/159) |
| 160 | **UI-015** — rememberAlertDialogIosProperties does not remember changes to textFields | Low | S | UI-012 | open | [#160](https://github.com/Apdelrahman1911/nativeCmpkit/issues/160) |
| 161 | **UI-039** — Internal expandable FAB loses expanded items on model updates and is not ready for public exposure | Low | M | — | open | [#161](https://github.com/Apdelrahman1911/nativeCmpkit/issues/161) |
| 162 | **UI-041** — Liquid button eagerly builds an unused highlight shader and lacks a measured effects budget | Low | M | — | open | [#162](https://github.com/Apdelrahman1911/nativeCmpkit/issues/162) |
| 163 | **UI-043** — A delayed Cupertino button release animation can clear the next press highlight | Low | S | — | open | [#163](https://github.com/Apdelrahman1911/nativeCmpkit/issues/163) |
| 164 | **UI-044** — Cupertino activity indicator ignores input alpha and draws the first spoke twice | Low | S | — | open | [#164](https://github.com/Apdelrahman1911/nativeCmpkit/issues/164) |
| 165 | **Upstream #259** — [Low][Upstream #259] Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | Low | triage-first | — | open | [#165](https://github.com/Apdelrahman1911/nativeCmpkit/issues/165) |
| 166 | **Upstream #78** — [Low][Upstream #78] Contacts and OTP feature | Low | triage-first | — | open | [#166](https://github.com/Apdelrahman1911/nativeCmpkit/issues/166) |
| 167 | **Upstream #471** — [Low][Upstream #471] Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | Low | triage-first | — | open | [#167](https://github.com/Apdelrahman1911/nativeCmpkit/issues/167) |
| 169 | **Upstream #343** — [Low][Upstream #343] Support native file preview | Low | triage-first | — | open | [#169](https://github.com/Apdelrahman1911/nativeCmpkit/issues/169) |
| 170 | **Upstream #72** — [Low][Upstream #72] Zoom in/out in browser | Low | triage-first | — | open | [#170](https://github.com/Apdelrahman1911/nativeCmpkit/issues/170) |
