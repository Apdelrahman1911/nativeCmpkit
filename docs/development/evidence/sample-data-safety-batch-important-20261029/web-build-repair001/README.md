# Shared Web build ownership repair — 2026-10-30

Original Linux build-only40971665663/539ddc64 **FAILED**, Gradle1/1993.47s,
zero tests requested. The actual Wasm webpack process selected Node26.2.0 while
only the root modern spec was pinned24.16.0. Both input snapshots hold960 exact
Git inputs; four real compilation graphs omit the targeted Navigation groups
and preserve minSdk24. The old all-or-nothing output observer lost its earlier
per-target values when Wasm output was missing: do not infer accepted Android,
JVM or JS output hashes from that failed aggregate.

[Actual KGP routing](kgp-routing-review.json) inspects the cached2.4.20 bytecode:
NpmProject/webpack reads its own project's modern spec; its default version
convention reads the separate legacy root version26.2.0. A root-only24.16.0 pin
therefore does not bind the project executable. The minimal repair registers
NodeJsPlugin/WasmNodeJsPlugin callbacks in **allprojects**, pinning every
late-created public modern spec without mutating deprecated KGP internals.
The existing Kotlin/Compose/AGP/Node/Yarn pins and frozen locks are not lowered.

Shared sample verification now records public Gradle outcomes separately for
all six Linux/two Apple requested build tasks. Output observers retain each
nonempty target hash and failure separately; missing/foreign/stale/failed/skipped/
NO-SOURCE task receipts still fail that target and the whole batch. Valid
UP-TO-DATE/FROM-CACHE compilations may be reused, **never counted as fresh tests**.
Daemon, graph, output and Node observers are isolated: one refusal cannot erase
other observations. Two actual webpack doFirst witnesses execute the selected
root/project spec's public executable with --version and retain only safe
version/path/hash metadata; no PATH-node substitute or private field reflection.

[Shared important checks](important001.json): **86/86 synthetic owning methods**,
all963 selected inputs held. These overlap the preceding shared tools; they are
not additive unique functions or Gradle/browser/native/sample executions.
[Five-method red](red001.json) preserves two failures/ten error events (including
subcases). The first actionlint caller used nonexistent validate.yml after the
86 methods passed; [correct actual-workflow lint](lint-final001.json) and
whitespace pass without method replay. No new local heavy builds below8GiB.

Hosted recovery must use an immutable revision and request **builds only**, not
repeat the50 Linux/17 Apple completed sample methods. Apple40974963662 remains
independently running on535b0353; do not cancel, modify or redispatch it.
#100/NAV-013 and #154/NAV-016 remain open pending their original criteria.
Sample evidence is never library coverage, and the host-C allocation discovery
is not UIKit/library/GC/leak evidence. Single-agent/max2 queued+running heavy
requests/8GiB reserve; no publishing, Pages, main/history or independent
native/minimum/ABI/consumer/legal/dependency/security/release gate changes.
