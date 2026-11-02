# Finite Desktop verification batches

## Current missing-only amendment — 2026-11-02

The later [candidate originals363–372](evidence/current-platform-recovery-20261101/javafx-native-egl363-372/README.md)
accept macOS ARM64 Stop1/1; **never replay that accepted method**. Linux ARM64
fails before Stop because Skiko lacks `libEGL.so.1`; the exact Linux-only runtime
prerequisite is repaired and only its failed Stop method should run next.
macOS x64 is already requested once on924a06c2; review its originals when terminal.
These later observations supersede the three-Stops-pending statement below.
Ordinary dependency adoption/legal/security/consumer/API–ABI still remain separate.

The original Windows request-state method and the private full-JAR candidate's
original Windows Stop method are accepted and **must not be replayed via the
Windows-single alias**. [Linux originals346–349](evidence/current-platform-recovery-20261101/desktop-linux-native346-349/README.md)
now accept x64 request1 and ARM64 request/302-Reload2; only ARM64 Stop fails.
**Never dispatch the old Linux-pair alias again:** it would replay those three
unchanged accepted methods. Only an owning correction and failed-only Stop1
verification is appropriate. [macOS originals350–354](evidence/current-platform-recovery-20261101/desktop-macos-native350-354/README.md)
now accept both request methods; both Stops still fail. **Never dispatch the old
macOS-pair alias again.** Only Linux ARM64 Stop and the two macOS Stops remain
in this cohort; select each failed method on its actual host after an owning
correction. At most two combined hosted reservations include queued work.
Ordinary JavaFX adoption remains separate
from the private Stop acceptance. The [JS1/Wasm1 offline destination result](evidence/current-platform-recovery-20261101/browser-android317-319/README.md)
is now accepted, not pending or system-offline certification. Other security/
consumer/API-ABI/corresponding-source/legal requirements remain unchanged. Earlier
expected/missing counts below describe their preparation date, not current results.

The full Desktop routes remain unchanged. Five additive aliases make the missing
work dispatchable under the **two combined hosted-heavy row** limit. A queued or
reserved matrix row counts even when `max-parallel` is one.

| Profile | Exact hosts, in order | Required executions / original XML |
| --- | --- | --- |
| `webview-desktop-request-state-linux-pair` | Linux x64, Linux ARM64 | 4 / 3 |
| `webview-desktop-request-state-macos-pair` | macOS ARM64, macOS x64 | 4 / 4 |
| `webview-desktop-request-state-windows-single` | Windows x64 | 2 / 2 |
| `webview-desktop-security-linux-arm64-windows-pair` | Windows x64, Linux ARM64 | 7 / 7 |
| `webview-desktop-security-macos-pair` | macOS ARM64, macOS x64 | 6 / 6 |

Request aliases partition the ten missing #64 executions. Security aliases
partition the thirteen remaining security executions and exclude the accepted
Linux x64 TLS case. These are expected counts, **not native results**.

## Admission and execution

Current failed-only candidate verification uses the dedicated
`javafx-library-candidate.yml`, one `platform=linux-arm64`, `macos-arm64` or
`macos-x64` host per dispatch. The original Stop1/XML1/native predicates remain.
[Owning351–361](evidence/current-platform-recovery-20261101/javafx-platform-candidate351-361/README.md)
qualified source/packaging at its dated checkpoint; later native acceptance is
the current amendment above. Only the unaccepted host outcomes remain required.
Both JavaFX native workflows are manual-only; accepted Windows/Linux cases are
not automatically replayed by the added classifier pins.

- `scripts/ci/workflow_matrix.py` inherits fresh rows from each canonical parent.
  Exact slot tuple/order, suite, module, runner and architecture are checked.
  Caller mutation cannot alter a parent or a later invocation.
- The shared workflow exposes only the five fixed names. Security aliases invoke
  the unchanged collector with canonical
  `--profile webview-desktop-security-regressions --slot "$SLOT"` arguments.
- Native steps, artifact allowlists, minimum token permissions, cache ownership
  and the serial-one/default-two expression are unchanged. No new graph or
  dependency-trust result follows from an alias or an equal cache key.
- Do not dispatch either old four/five-row route under the current reservation
  limit. Dispatch a pair only when both global slots are free; a single may
  coexist with one other single.

## Verification

[Owning evidence104](evidence/current-platform-recovery-20261101/desktop-finite-alias-owning104/README.md)
records six reversible fragments in three existing files and one nine-method
control addition. Nine new alias-specific controls and one changed owning guard
passed **10/10 once**, 0.390723s, with 1147 library /1223 combined inputs held.
The new controls cover the expanded choice/cache populations without replaying
old all-profile loops. A wrong private packet prefix was refused before edits or
tests and recovered only as custody bookkeeping.

No Desktop native method or graph collector had run for these aliases at that
dated preparation checkpoint; current native acceptance is amended above.
Source/model success does not establish platform behavior, loaded native bytes,
resource lifetime, packaged consumers, security, ABI or release readiness.
