# Related sample platform verification candidate — 2026-10-29

Prepared **one Linux host** for actual Android app/JVM jar/JS and Wasm
production bundles, four real main-compilation dependency graphs and **50 new
platform executions** (16 Android-host, 17 JS, 17 Wasm). A later **one Apple
host** selects 17 iOS-simulator sample cases, both device/simulator `Common`
frameworks, real Xcode target/scheme enumeration and the unsigned actual `Calf`
Swift application/framework shell phase. Neither mode is dispatched implicitly.

The four already accepted Skia codec method bodies moved byte-identically from
`desktopTest` to the existing `nonAndroidTest` hierarchy. Desktop outcomes are
reused, **not replayed**. Three new Android native-graphics Robolectric methods
exercise real PNG ownership/roundtrip/crop, invalid bytes and encoding a recycled
bitmap; **host graphics are not Android physical-device evidence**. Existing
common owner/bounds methods execute freshly only on previously unaccepted hosts.
This is sample evidence, never a substitute for library integration tests.

The original codec-source guard failed 1/1 before the owning move. The initial
836-method CI-tool sweep remains **FAILED: 835 pass/one stale cache-count guard**.
It exposed a second guard that still assumed three caches. Both guards now name
the exact library cache rather than depend on job order; all four caches retain
exact declaration/runtime keys, no prefix fallback and no test/output caching.
The final changed owning check passes **81/81** with **960 held sample/library/
workflow inputs**; those methods overlap the initial sweep, not 917 distinct
passes. Workflow actionlint and whitespace pass. **ZERO local Gradle, native,
codec or library tests** were executed; root free space is below the 8 GiB reserve.

A separate new screen-pair reducer guard also failed before repair: actual runtime
receipts intentionally expose `device_type`, not private/user-assigned `name`.
The reducer now checks public exact iPad/iPhone type prefixes and boot state.
This changes tooling only; it does not alter or redispatch running immutable
40956332036, waive either screen/pixel assertion or replay an accepted native case.
Any failure in that original reducer must stay recorded independently of the
actual fresh native tests. The final 81 includes its seven owning screen guards.

**#100/NAV-013 and #154/NAV-016 remain open.** Complete graph/target review is
still required for NAV-016; sample minSdk24 has not been lowered. NAV-013 additionally
requires actual selection/export/UI lifecycle, provider failure, bounded large
selection and representative memory/responsiveness measurements. Compilation or
four codec passes cannot replace them. NAV-011 provenance/availability and NAV-012
real secure-input/log acceptance remain open too. No issue/release certification,
package upload, registry publication, Pages or main/history change occurs here.
