# Complete ordered backlog

Generated from every audit finding plus actionable historical requests. See [roadmap strategy](README.md), [machine-readable tests/dependencies](backlog.json), and [finding detail](../audit/findings-index.md). State is the last synchronized observation, not a live tracker.

## 0. Migration remediation already verified

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 1 | **BUILD-003** — Any nonempty prebuilt native subdirectory suppresses every local native build | High | M | — | open | [draft](../audit/issue-drafts/audit-BUILD-003.md) |
| 2 | **BUILD-008** — Release version input is embedded directly in executable shell scripts | Medium | S | — | closed | [draft](../audit/issue-drafts/audit-BUILD-008.md) |
| 3 | **BUILD-009** — Pinned JetBrains-only daemon prevents use of installed JDK 17 and contradicts CI setup | Medium | S | — | closed | [draft](../audit/issue-drafts/audit-BUILD-009.md) |
| 4 | **BUILD-011** — Release staging duplicates both native libraries into both desktop artifacts | Low | S | BUILD-003 | closed | [draft](../audit/issue-drafts/audit-BUILD-011.md) |

## 1. Before a supported preview

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 5 | **BUILD-001** — Desktop WebView POM hard-codes the publisher OS in JavaFX dependencies | High | L | — | open | [draft](../audit/issue-drafts/audit-BUILD-001.md) |
| 6 | **BUILD-006** — Verification pipeline does not gate platform behavior, consumer compatibility, or native correctness | High | XL | — | open | [draft](../audit/issue-drafts/audit-BUILD-006.md) |
| 7 | **IO-001** — iOS byte-array reads can overrun native destination memory and mishandle empty files | High | S | — | open | [draft](../audit/issue-drafts/audit-IO-001.md) |
| 8 | **IO-002** — Android saver loses pending content across recomposition and can report an empty export as success | High | M | — | open | [draft](../audit/issue-drafts/audit-IO-002.md) |
| 9 | **IO-003** — Desktop composition disposal races raw JNI handles; cancelled creation can leak handles | High | L | — | open | [draft](../audit/issue-drafts/audit-IO-003.md) |
| 10 | **IO-004** — Desktop save can delete its own source and does not reliably replace existing content | High | M | — | open | [draft](../audit/issue-drafts/audit-IO-004.md) |
| 11 | **NATIVE-001** — Desktop stopLoading re-enqueues itself instead of cancelling WebEngine loading | High | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-001.md) |
| 12 | **NATIVE-002** — Android and Desktop WebViews retain live native views after composition disposal | High | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-002.md) |
| 13 | **NATIVE-010** — Enabling Web JavaScript removes all iframe isolation for inline HTML | High | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-010.md) |
| 14 | **NATIVE-013** — Desktop CookieManager overwrites JavaFX and application-global cookie handlers | High | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-013.md) |
| 15 | **NATIVE-019** — Android camera loses its output URI across Activity/process recreation | High | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-019.md) |
| 16 | **NATIVE-027** — Desktop share fallback opens arbitrary files/URLs instead of offering an explicit sharing fallback | High | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-027.md) |
| 17 | **NAV-001** — Adaptive navigation silently discards per-navigation arguments | High | L | — | open | [draft](../audit/issue-drafts/audit-NAV-001.md) |
| 18 | **NAV-002** — Route-keyed saved state aliases duplicate back-stack entries and incompletely fixes #542 | High | L | NAV-001 | open | [draft](../audit/issue-drafts/audit-NAV-002.md) |
| 19 | **NAV-009** — Embedded Cupertino font requires MIT notices in distributed artifacts; baseline notice gap partially repaired | High | M | — | open | [draft](../audit/issue-drafts/audit-NAV-009.md) |
| 20 | **PERM-011** — iOS calendar uses the iOS17 full-access API without availability gating or matching usage descriptions | High | M | — | open | [draft](../audit/issue-drafts/audit-PERM-011.md) |
| 21 | **PERM-018** — Android LocationTracker never updates its public location states | High | M | — | open | [draft](../audit/issue-drafts/audit-PERM-018.md) |
| 22 | **UI-001** — iOS date state and native calendars do not enforce the documented UTC-day/year-range contract | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-001.md) |
| 23 | **UI-002** — Native date conversion treats user-calendar components as Gregorian dates | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-002.md) |
| 24 | **UI-012** — Presented iOS alerts update their text but retain original action and text-field callbacks | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-012.md) |
| 25 | **UI-013** — iOS action sheets are presented without an iPad popover anchor | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-013.md) |
| 26 | **UI-014** — Alert dismissal during presentation is dropped and cleanup shares user-dismiss callbacks | High | L | — | open | [draft](../audit/issue-drafts/audit-UI-014.md) |
| 27 | **UI-020** — Native bar measurement permanently stops after several stable frames | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-020.md) |
| 28 | **UI-021** — Native bars live outside the Compose layout/transition hierarchy | High | L | UI-020 | open | [draft](../audit/issue-drafts/audit-UI-021.md) |
| 29 | **UI-027** — Liquid Glass slider retains stale enabled, range, geometry and direction inside drag callbacks | High | M | — | open | [draft](../audit/issue-drafts/audit-UI-027.md) |
| 30 | **UI-040** — calf-ui test coverage omits all native managers and most interactive control families | High | L | — | open | [draft](../audit/issue-drafts/audit-UI-040.md) |
| 31 | **BUILD-004** — Packaged native platform matrix omits Linux arm64 and Windows arm64 paths expected by loaders | Medium | L | BUILD-003 | open | [draft](../audit/issue-drafts/audit-BUILD-004.md) |
| 32 | **BUILD-005** — Native release binaries have unlocked Rust dependencies and a floating compiler | Medium | M | — | open | [draft](../audit/issue-drafts/audit-BUILD-005.md) |
| 33 | **BUILD-007** — Dependency and workflow trust is not reproducibly verified beyond the wrapper | Medium | L | — | open | [draft](../audit/issue-drafts/audit-BUILD-007.md) |
| 34 | **IO-008** — Picked-file access lifetime is not represented for security-scoped folders or persisted Android URIs | Medium | L | — | open | [draft](../audit/issue-drafts/audit-IO-008.md) |
| 35 | **IO-005** — iOS saver exports the original source with move semantics and ignores requested file names | High | M | IO-008 | open | [draft](../audit/issue-drafts/audit-IO-005.md) |
| 36 | **PERM-001** — Android silently treats an unregistered Permission as granted | Medium | M | — | open | [draft](../audit/issue-drafts/audit-PERM-001.md) |
| 37 | **PERM-002** — Android bulk results are assigned to the first global permission alias, not the requested permissions | High | M | PERM-001 | open | [draft](../audit/issue-drafts/audit-PERM-002.md) |
| 38 | **PERM-003** — Android bulk/child permission requests do not consistently deliver completion callbacks | Medium | M | PERM-002 | open | [draft](../audit/issue-drafts/audit-PERM-003.md) |
| 39 | **PERM-004** — Android location requests do not orchestrate fine/coarse and foreground/background prerequisites | High | L | PERM-003 | open | [draft](../audit/issue-drafts/audit-PERM-004.md) |
| 40 | **PERM-005** — Remembered permission objects retain obsolete result callbacks after recomposition | Medium | S | — | open | [draft](../audit/issue-drafts/audit-PERM-005.md) |
| 41 | **PERM-007** — iOS result callbacks are not main-thread/disposal safe and run before status refresh | Medium | L | PERM-005 | open | [draft](../audit/issue-drafts/audit-PERM-007.md) |
| 42 | **PERM-009** — iOS BackgroundLocation cannot upgrade an existing WhenInUse grant to Always | High | M | PERM-007 | open | [draft](../audit/issue-drafts/audit-PERM-009.md) |
| 43 | **PERM-008** — iOS multi-permission launch is concurrent and returns singleton results rather than a complete batch | High | L | PERM-003, PERM-007, PERM-009 | open | [draft](../audit/issue-drafts/audit-PERM-008.md) |
| 44 | **PERM-013** — iOS Wi-Fi status observation publishes a Bonjour service and conflates timeout/cancellation with denial | High | L | PERM-007 | open | [draft](../audit/issue-drafts/audit-PERM-013.md) |
| 45 | **PERM-020** — Android LocationTracker rebinding has no ownership boundary or coroutine cleanup | Medium | M | PERM-018 | open | [draft](../audit/issue-drafts/audit-PERM-020.md) |
| 46 | **PERM-021** — Android LocationTracker suppresses missing-permission checks and ignores provider failures | High | L | PERM-018, PERM-020 | open | [draft](../audit/issue-drafts/audit-PERM-021.md) |
| 47 | **UI-016** — iOS sheet programmatic transitions bypass confirmValueChange and skipHiddenState | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-016.md) |
| 48 | **UI-017** — iOS sheet state never tracks partial detents or interactive dismissal and uses reversed detent order | Medium | M | UI-016 | open | [draft](../audit/issue-drafts/audit-UI-017.md) |
| 49 | **UI-018** — Sheet operation cancellation and disposal can leave native presentation and retained owners behind | High | L | UI-016, UI-017 | open | [draft](../audit/issue-drafts/audit-UI-018.md) |
| 50 | **UI-030** — Liquid Glass switch can visually diverge from its controlled checked value | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-030.md) |
| 51 | **UI-029** — Liquid Glass slider and switch lack actionable accessibility and keyboard semantics | High | M | UI-030 | open | [draft](../audit/issue-drafts/audit-UI-029.md) |
| 52 | **UI-031** — Cancelled pointer gestures can commit a Liquid Glass switch toggle | High | M | UI-030 | open | [draft](../audit/issue-drafts/audit-UI-031.md) |
| 53 | **BUILD-002** — Pinned JavaFX media 19 matches a published low-severity security advisory | Low | M | BUILD-001 | open | [draft](../audit/issue-drafts/audit-BUILD-002.md) |
| 54 | **BUILD-010** — Desktop resource processing always invokes an untracked release-mode Cargo build | Low | M | BUILD-003, BUILD-005 | open | [draft](../audit/issue-drafts/audit-BUILD-010.md) |
| 55 | **BUILD-012** — Resolved Linux picker graph contains three newly unmaintained D-Bus crates | Low | M | BUILD-005 | open | [draft](../audit/issue-drafts/audit-BUILD-012.md) |

## 2. Compatibility, robustness and performance

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 56 | **IO-006** — Save write failures can report success or escape without a completion/error result | Medium | L | IO-002, IO-004, IO-005 | open | [draft](../audit/issue-drafts/audit-IO-006.md) |
| 57 | **IO-007** — iOS picker completion is not exactly once and document swipe dismissal is not observed | Medium | M | — | open | [draft](../audit/issue-drafts/audit-IO-007.md) |
| 58 | **IO-009** — Browser file reads treat DONE as success and do not cancel or propagate FileReader failures | Medium | M | — | open | [draft](../audit/issue-drafts/audit-IO-009.md) |
| 59 | **IO-010** — File-kind queries misclassify extensionless browser files and nonexistent paths | Medium | S | — | open | [draft](../audit/issue-drafts/audit-IO-010.md) |
| 60 | **IO-011** — Web saver accepts onResult but never calls it or exposes download-only capability | Medium | L | — | open | [draft](../audit/issue-drafts/audit-IO-011.md) |
| 61 | **IO-012** — Immediate web Blob URL revocation can race the browser download | Medium | S | — | open | [draft](../audit/issue-drafts/audit-IO-012.md) |
| 62 | **IO-013** — iOS picked-file copies have no ownership cleanup and are created before result limits are applied | Medium | L | IO-007, IO-008 | open | [draft](../audit/issue-drafts/audit-IO-013.md) |
| 63 | **IO-014** — Portable path/name metadata exposes encoded or unreadable references instead of the readable file | Medium | M | IO-008 | open | [draft](../audit/issue-drafts/audit-IO-014.md) |
| 64 | **IO-015** — Desktop MIME filtering omits modern image formats and silently disables unknown custom filters | Medium | M | — | open | [draft](../audit/issue-drafts/audit-IO-015.md) |
| 65 | **IO-017** — Some remembered launchers retain stale selection limits, image representation and parent windows | Medium | S | IO-003 | open | [draft](../audit/issue-drafts/audit-IO-017.md) |
| 66 | **IO-018** — Multiple selection accepts invalid limits and differs across platform fallback paths | Medium | M | — | open | [draft](../audit/issue-drafts/audit-IO-018.md) |
| 67 | **IO-019** — Android folder selections are wrapped using single-document metadata and stream-based existence | Medium | M | IO-008, IO-010 | open | [draft](../audit/issue-drafts/audit-IO-019.md) |
| 68 | **IO-020** — Android whole-file read leaks its input stream if reading fails | Medium | S | — | open | [draft](../audit/issue-drafts/audit-IO-020.md) |
| 69 | **IO-021** — Coil fetches eagerly copy whole files and the byte-array API needs explicit scheduling/size guidance | Medium | L | IO-001, IO-020 | open | [draft](../audit/issue-drafts/audit-IO-021.md) |
| 70 | **IO-023** — Native parent-window pointers have unproven lifetime and thread-affinity guarantees | Medium | L | IO-003, IO-017 | open | [draft](../audit/issue-drafts/audit-IO-023.md) |
| 71 | **IO-024** — JNI path conversion silently replaces non-Unicode filenames | Medium | M | IO-006 | open | [draft](../audit/issue-drafts/audit-IO-024.md) |
| 72 | **IO-025** — iOS Document filter maps an application MIME wildcard to the application-bundle UTI | Medium | M | IO-015 | open | [draft](../audit/issue-drafts/audit-IO-025.md) |
| 73 | **IO-026** — Web picker catches application callback failures as cancellation and lacks disposal cleanup | Medium | M | — | open | [draft](../audit/issue-drafts/audit-IO-026.md) |
| 74 | **NATIVE-003** — Android and iOS onCreated run before the advertised native WebView reference exists | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-003.md) |
| 75 | **NATIVE-004** — Web state-driven URL loading does not clear existing iframe srcdoc | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-004.md) |
| 76 | **NATIVE-005** — WebView request state is not reset consistently on Desktop, iOS and Web | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-005.md) |
| 77 | **NATIVE-006** — Web WebView never invokes onDispose and retains iframe/listener references | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-006.md) |
| 78 | **NATIVE-007** — Non-Android saveable WebView state restores metadata but no content | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-007.md) |
| 79 | **NATIVE-008** — Replay-one navigation flow replays transient back/forward/stop commands on reattachment | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-008.md) |
| 80 | **NATIVE-009** — iOS captureBackPresses=false is overridden by settings and URL loads | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-009.md) |
| 81 | **NATIVE-011** — Browser CookieManager silently misrepresents URL, expiry, HttpOnly and deletion support | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-011.md) |
| 82 | **NATIVE-012** — Desktop and iOS getCookies do not implement full request-URL cookie matching | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-012.md) |
| 83 | **NATIVE-014** — Desktop cookie expiry is recalculated from read time and drifts into the future | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-014.md) |
| 84 | **NATIVE-015** — JavaScript evaluation has inconsistent failure, result and thread semantics | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-015.md) |
| 85 | **NATIVE-016** — Common WebContent options are silently ignored on several targets | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-016.md) |
| 86 | **NATIVE-017** — iOS inline-media configuration is changed only after WKWebView construction | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-017.md) |
| 87 | **NATIVE-018** — Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-018.md) |
| 88 | **NATIVE-020** — Camera callback/lifetime handling is unstable across recomposition | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-020.md) |
| 89 | **NATIVE-021** — Camera API silently drops unsupported, cancelled and failed operations | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-021.md) |
| 90 | **NATIVE-022** — Android camera hardcodes a host FileProvider authority without public setup or validation | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-022.md) |
| 91 | **NATIVE-023** — iOS camera has no in-flight presentation guard or lifecycle-bound cleanup | Medium | M | NATIVE-020 | open | [draft](../audit/issue-drafts/audit-NATIVE-023.md) |
| 92 | **NATIVE-024** — Camera capture does synchronous full-resolution PNG work and has no temporary-file ownership policy | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-024.md) |
| 93 | **NATIVE-025** — ShareResult.Success means chooser launch/service selection rather than completed sharing on some targets | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-025.md) |
| 94 | **NATIVE-026** — Web clipboard fallback reports success before its promise resolves | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-026.md) |
| 95 | **NATIVE-028** — Android file sharing forwards file:// URIs without FileProvider conversion | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-028.md) |
| 96 | **NATIVE-029** — macOS share leaks both the Objective-C delegate and its Arc completion state on every presented picker | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-029.md) |
| 97 | **NATIVE-030** — macOS sharing blocks a coroutine worker for up to five minutes without cancellation integration | Medium | L | NATIVE-029 | open | [draft](../audit/issue-drafts/audit-NATIVE-030.md) |
| 98 | **NATIVE-031** — Desktop native share extraction uses one mutable filename across versions, architectures and processes | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-031.md) |
| 99 | **NATIVE-032** — Share callbacks can be delivered twice when application result handling throws | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-032.md) |
| 100 | **NATIVE-033** — Public mobile launch/evaluation operations lack an explicit main-thread contract or enforcement | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-033.md) |
| 101 | **NATIVE-037** — Replacing WebViewState or native lifecycle callbacks at the same composable identity is not safely rebound | Medium | M | NATIVE-002, NATIVE-006 | open | [draft](../audit/issue-drafts/audit-NATIVE-037.md) |
| 102 | **NATIVE-038** — Android enables multiple WebView windows but supplies no window-creation handler | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-038.md) |
| 103 | **NAV-003** — NavArgument builder rejects missing/null defaults and accepts mismatched typed defaults | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NAV-003.md) |
| 104 | **NAV-004** — AdaptiveBundle violates documented runtime type and fallback contracts | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NAV-004.md) |
| 105 | **NAV-005** — AdaptiveNavType inference and serialization are incomplete and not reliably round-trippable | Medium | M | NAV-003, NAV-004 | open | [draft](../audit/issue-drafts/audit-NAV-005.md) |
| 106 | **NAV-006** — AdaptiveNavHost retains stale graph closures and does not initialize a replacement controller | Medium | M | NAV-001, NAV-002 | open | [draft](../audit/issue-drafts/audit-NAV-006.md) |
| 107 | **NAV-007** — Unknown routes and duplicate graph registrations silently render blank or select the first definition | Medium | M | NAV-001 | open | [draft](../audit/issue-drafts/audit-NAV-007.md) |
| 108 | **NAV-008** — Navigation exposes two incompatible controller abstractions and lacks a declared platform capability contract | Medium | L | — | open | [draft](../audit/issue-drafts/audit-NAV-008.md) |
| 109 | **NAV-010** — CupertinoIcon leaves the private-use glyph Text semantics exposed | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NAV-010.md) |
| 110 | **NAV-011** — Generated icon/symbol catalogues lack a reproducible generator and Apple availability metadata | Medium | M | NAV-009 | open | [draft](../audit/issue-drafts/audit-NAV-011.md) |
| 111 | **NAV-012** — Sample secure password text field logs every entered value | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NAV-012.md) |
| 112 | **NAV-013** — Sample image export runs unbounded reads and image allocations without error or concurrency control | Medium | M | — | open | [draft](../audit/issue-drafts/audit-NAV-013.md) |
| 113 | **NAV-014** — Streaming sample cancellation does not interrupt its synchronous read loop | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NAV-014.md) |
| 114 | **NAV-015** — Android sample permission menu and manifest disagree and declare unrelated broad permissions | Medium | S | — | open | [draft](../audit/issue-drafts/audit-NAV-015.md) |
| 115 | **NAV-018** — Derived Apache-2.0 source attribution needs reconstruction and artifact verification | Medium | M | NAV-008 | open | [draft](../audit/issue-drafts/audit-NAV-018.md) |
| 116 | **PERM-006** — Permission lifecycle refresh skips previously granted permissions, leaving revocations stale | Medium | M | PERM-013 | open | [draft](../audit/issue-drafts/audit-PERM-006.md) |
| 117 | **PERM-010** — iOS location delegates consume pending requests on nonterminal events and overwrite overlapping callbacks | Medium | M | PERM-007, PERM-009 | open | [draft](../audit/issue-drafts/audit-PERM-010.md) |
| 118 | **PERM-012** — iOS WriteCalendar requests full read/write access and rejects write-only authorization | Medium | M | PERM-011 | open | [draft](../audit/issue-drafts/audit-PERM-012.md) |
| 119 | **PERM-014** — iOS Bluetooth request lifetime and completion need device-backed hardening | Medium | M | PERM-007 | open | [draft](../audit/issue-drafts/audit-PERM-014.md) |
| 120 | **PERM-015** — iOS RemoteNotification skips APNs registration when notification authorization already exists | Medium | M | PERM-007 | open | [draft](../audit/issue-drafts/audit-PERM-015.md) |
| 121 | **PERM-016** — PermissionStatus loses partial capability, precision and requestability distinctions | Medium | L | — | open | [draft](../audit/issue-drafts/audit-PERM-016.md) |
| 122 | **PERM-017** — Desktop, JS and Wasm permissions are nonfunctional stubs with silent callbacks | Medium | L | PERM-016 | open | [draft](../audit/issue-drafts/audit-PERM-017.md) |
| 123 | **PERM-019** — Non-Android geolocation trackers only print messages and report fabricated zero coordinates | Medium | XL | PERM-018 | open | [draft](../audit/issue-drafts/audit-PERM-019.md) |
| 124 | **PERM-022** — Android geo data treats missing accuracy/speed/bearing/altitude as real zero measurements | Medium | M | PERM-018 | open | [draft](../audit/issue-drafts/audit-PERM-022.md) |
| 125 | **PERM-024** — Storage guidance asks for all-files access that WriteStorage never requests or verifies | Medium | S | — | open | [draft](../audit/issue-drafts/audit-PERM-024.md) |
| 126 | **UI-003** — Replacing iOS date state can skip initialization effects for the new native picker | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-003.md) |
| 127 | **UI-004** — Empty or reversed date-bound intersections reach native interval APIs without a defined policy | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-004.md) |
| 128 | **UI-006** — Compact Material date dialog can commit stale or newly forbidden scratch selections | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-006.md) |
| 129 | **UI-007** — Native range highlighting eagerly allocates every day of a selected range on the UI path | Medium | L | — | open | [draft](../audit/issue-drafts/audit-UI-007.md) |
| 130 | **UI-009** — Time-state constructor checks the hour twice and never validates the minute on iOS | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-009.md) |
| 131 | **UI-010** — Remembered native time picker keeps writing to the original state after replacement | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-010.md) |
| 132 | **UI-019** — Changing the sheet confirmation callback recreates remembered sheet state | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-019.md) |
| 133 | **UI-022** — Clearing native navigation-bar items leaves the previous tabs visible | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-022.md) |
| 134 | **UI-023** — iOS toolbar does not implement its documented Material fallback | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-023.md) |
| 135 | **UI-024** — Dropdown availability check rejects later iOS major versions and selects a private-gesture fallback | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-024.md) |
| 136 | **UI-025** — Native dropdown reports dismissal immediately after opening and cannot follow expanded=false | Medium | M | UI-024 | open | [draft](../audit/issue-drafts/audit-UI-025.md) |
| 137 | **UI-026** — Material dropdown silently drops most public popup and styling parameters | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-026.md) |
| 138 | **UI-032** — Liquid Glass slider arithmetic does not guard zero-length or invalid numeric ranges | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-032.md) |
| 139 | **UI-028** — AdaptiveSlider drops discrete steps on the iOS26 Liquid Glass branch | Medium | M | UI-029, UI-032 | open | [draft](../audit/issue-drafts/audit-UI-028.md) |
| 140 | **UI-033** — Cupertino slider accessibility snapping fails for negative target values | Medium | S | — | open | [draft](../audit/issue-drafts/audit-UI-033.md) |
| 141 | **UI-034** — Cupertino slider gesture state has incomplete keys and uncancelled competing tap animations | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-034.md) |
| 142 | **UI-035** — Several iOS adaptive visual and interaction parameters are accepted but unused | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-035.md) |
| 143 | **UI-036** — ImageVector-to-UIImage conversion discards vector paints, transforms and clipping | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-036.md) |
| 144 | **UI-037** — Bitmap-to-UIImage bridge has unverified byte-order, premultiplication and buffer-lifetime assumptions | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-037.md) |
| 145 | **UI-038** — Native image conversion leaks CoreGraphics resources on the image-creation failure path | Medium | S | UI-037 | open | [draft](../audit/issue-drafts/audit-UI-038.md) |
| 146 | **UI-042** — Damped drag animation launches overlapping jobs per update and tracks velocity with wall-clock time | Medium | M | UI-031, UI-032 | open | [draft](../audit/issue-drafts/audit-UI-042.md) |
| 147 | **UI-045** — Applying a native view theme also mutates its parent view style | Medium | M | — | open | [draft](../audit/issue-drafts/audit-UI-045.md) |
| 168 | **Upstream #34** — [Medium][Upstream #34] Camera issue in webview iOS | Medium | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-1f275157ca9474140c77.md) |

## 3. Breadth, polish and longer-term design

| Order | Finding / topic | Priority | Effort | Dependencies | State | Issue |
|---:|---|---|---|---|---|---|
| 148 | **IO-016** — MIME lookup is locale-sensitive, parses only comma-space lists, and allocates per entry | Low | S | — | open | [draft](../audit/issue-drafts/audit-IO-016.md) |
| 149 | **IO-022** — Native cache fallback can lose user isolation and loader trusts external search paths | Low | M | — | open | [draft](../audit/issue-drafts/audit-IO-022.md) |
| 150 | **NATIVE-034** — Share subject is not delivered consistently and iOS assigns controller title instead of item subject | Low | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-034.md) |
| 151 | **NATIVE-035** — Maps, media and notification scaffolds must not be represented as implemented features | Low | L | — | open | [draft](../audit/issue-drafts/audit-NATIVE-035.md) |
| 152 | **NATIVE-036** — Desktop customUserAgent cannot be reset to its documented default using null | Low | S | — | open | [draft](../audit/issue-drafts/audit-NATIVE-036.md) |
| 153 | **NATIVE-039** — WebView settings changes and error accumulation perform avoidable full updates | Low | M | — | open | [draft](../audit/issue-drafts/audit-NATIVE-039.md) |
| 154 | **NAV-016** — Sample includes an unused second navigation library with an unnecessary compatibility burden | Low | S | NAV-008 | open | [draft](../audit/issue-drafts/audit-NAV-016.md) |
| 155 | **NAV-017** — Showcase reports a successful clipboard action that it never performs | Low | S | — | open | [draft](../audit/issue-drafts/audit-NAV-017.md) |
| 156 | **PERM-023** — Specify and test the numerical domain and undefined-bearing policy of LatLng | Low | S | — | open | [draft](../audit/issue-drafts/audit-PERM-023.md) |
| 157 | **UI-005** — Single-date state loses displayed-month intent on iOS and save/restore | Low | M | — | open | [draft](../audit/issue-drafts/audit-UI-005.md) |
| 158 | **UI-008** — No-selectable-day fallback is intentional but requires an explicit caller-visible validation policy | Low | S | — | open | [draft](../audit/issue-drafts/audit-UI-008.md) |
| 159 | **UI-011** — Native time picker ignores the public is24Hour preference | Low | S | — | open | [draft](../audit/issue-drafts/audit-UI-011.md) |
| 160 | **UI-015** — rememberAlertDialogIosProperties does not remember changes to textFields | Low | S | UI-012 | open | [draft](../audit/issue-drafts/audit-UI-015.md) |
| 161 | **UI-039** — Internal expandable FAB loses expanded items on model updates and is not ready for public exposure | Low | M | — | open | [draft](../audit/issue-drafts/audit-UI-039.md) |
| 162 | **UI-041** — Liquid button eagerly builds an unused highlight shader and lacks a measured effects budget | Low | M | — | open | [draft](../audit/issue-drafts/audit-UI-041.md) |
| 163 | **UI-043** — A delayed Cupertino button release animation can clear the next press highlight | Low | S | — | open | [draft](../audit/issue-drafts/audit-UI-043.md) |
| 164 | **UI-044** — Cupertino activity indicator ignores input alpha and draws the first spoke twice | Low | S | — | open | [draft](../audit/issue-drafts/audit-UI-044.md) |
| 165 | **Upstream #259** — [Low][Upstream #259] Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | Low | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-5098a291f843be33ed16.md) |
| 166 | **Upstream #78** — [Low][Upstream #78] Contacts and OTP feature | Low | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-5d3f0dfd1811a8c8d3dd.md) |
| 167 | **Upstream #471** — [Low][Upstream #471] Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | Low | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-80b18aaaa4c8a57bea15.md) |
| 169 | **Upstream #343** — [Low][Upstream #343] Support native file preview | Low | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-7a9f2e0f6e37e239b233.md) |
| 170 | **Upstream #72** — [Low][Upstream #72] Zoom in/out in browser | Low | triage-first | — | open | [draft](../audit/issue-drafts/upstream-topic-631f15a6c070ee5aadc9.md) |
