# Related picker ownership and exact-path batch — 2026-10-29

**IO-003/#6 and IO-024/#59 were closed together**, after reviewing every original
criterion against shared important tests and current owning source, before
archiving documentation. Original technical bodies, titles, labels and comments
are preserved. [IO-003 acceptance](closure/IO-003-acceptance.json),
[IO-024 acceptance](closure/IO-024-acceptance.json),
[both closure readbacks](closure/IO-003-verified-readback.json), and
[IO-024 readback](closure/IO-024-verified-readback.json) retain the exact scope.
Previous remaining requirements are archived, not erased from historical evidence.

## Actual results and safe reuse

The [lead review](lead-batch-source-results-review.json) deliberately records
both workflows as **FAILED**, despite the accepted owning results:

| Immutable run | Target | Actual Compose | Actual standalone path JNI |
| --- | --- | --- | --- |
| [40815285475](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40815285475), `04662845` | Linux x64 | 5/6; exit1/246.07s | 5/5; exit0/25s |
| Same first matrix | Windows x64 | 3/3; exit0/296.61s; three explicit Linux-only N/A | 1/1; exit0/36.06s |
| Same first matrix | macOS arm64 | Not executed after standalone failure | exit101/53.85s; original failure receipt retained |
| [40817067140](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40817067140), `95ac633a` | Linux x64 recovery | **6/6; exit0/244.07s** | **5/5; exit0/30.01s** |
| Same recovery | macOS arm64 | **3/3; exit0/314.72s**; three explicit Linux-only N/A | **1pass/4fail; exit101/79.73s** |

All selected target receipts bind838own-Git inputs and actual JDK17. Required
test identities, fresh XML, command exits, runtime, native payload and owned
portal shutdown were inspected. Reuse accepted Windows results rather than
repeating them. The ordinary real Unicode/supplementary JNI case passed on
macOS **inside the failed target**; it is not a green macOS JNI matrix.

**12 accepted Compose target executions of six authored methods and seven
accepted JNI path target executions of five authored methods.** They are not19
distinct functions, one green whole workflow or release-wide certification.
The [reuse review](reuse-owning-input-review.json) checks unchanged original
coroutine/JNI and native ownership code and the identical actual Linux native
payload. Prior Valgrind outcomes are not fresh executions; its48possible/
544reachable std/libtest bytes remain disclosed.

## Owning implementation and tests

- Real Compose window lifetime and packaged JNI cover cancellation before queued
  JNI entry, cancellation inside synchronous native creation, one allocation/one
  close, zero modal entry after observed cancellation, stale-ID rejection,
  overlapping-launch exclusion and a retained disposed launcher's refusal.
- Four native sessions snapshot2→5→unlimited→1, Java parent objects and current
  callbacks. Three Linux tests additionally launch the actual public factory in
  its first composition, operate real GTK dialogs, select/read exact owned file
  bytes, update visible-session settings/callbacks, close the actual host while
  the chooser is visible and close a registry ID while its show lease lives.
  Worker completion is awaited **after** host disposal.
- The private0700 D-Bus owns its actual FileChooser v3 frontend and GTK backend;
  it is not an existing user bus or mock. Readiness and all three clean unforced
  owned process shutdowns are checked. The driver now uses **PID AND exact title**:
  xdotool's default multi-property matching was OR. A real wrong-title negative
  calibration prevents repeating that fixture defect.
- Linux path tests use real invalid-byte files/directories, distinct valid
  replacement-character peers with different bytes, save-path failures, normal
  non-ASCII/emoji filenames and128 genuine mid-array JNI failures. Actual weak
  array witnesses collect while a retained positive control remains; typed
  IOException is cleared before ordinary JNI calls. JDK17 uses `-Xcheck:jni`,
  a64MiB heap and real owning converters, not a fake JNI environment.

Native parent0 is intentional. Java parent snapshots are **not** raw native
parent acquisition, AppKit thread affinity or window lifetime verification.
Three GTK cases are exact source-bound N/A on other hosts, not their OS chooser
tests. External Skiko AWT GUI initialization emitted a checked-JNI warning and
software-renderer fallback; standalone Linux converter checks were warning-free.
Do not claim whole GUI/JNI warning cleanliness.

## Failures, fixture domain and efficient recovery

Local `compose001` failed6/6 due missing test-host Skiko renderer. Immutable
`compose003` passed4/6 but exited1 from dialog lookup/cleanup failures. Those
actual failed XML outcomes remain. Corrected local immutable `b8e13521`
`picker-compose-immutable005` passed6/6, exit0/37.01s/838held inputs. Its original
task XML no longer exists at that local task path; the original collector receipt
is preserved rather than substituting a later XML. Other local dirty and
immutable JNI/Compose diagnostics are separately named and not release evidence.

All four macOS JNI failures are **before JNI** at invalid-name filesystem setup,
original `jni_path_tests.rs:65/67`, native EILSEQ92. The assumption that all Unix
filesystems admit arbitrary non-UTF8 filename bytes was false. Ordinary Unicode
already passed. Do not silently ignore those methods or claim nonexistent actual
selected files. The additive repair keeps Linux actual-file cases mandatory and
requires an actual macOS file+directory EILSEQ boundary plus four **controlled
unrepresentable PathBuf/real-JNI** cases with real valid peers. The dedicated
`build-native-libs.yml` profile `picker-jni-macos-domain` excludes accepted
Unicode/Compose/other hosts and unrelated SDK/Gradle/GUI setup; exact domain and
controlled-input markers, nonzero results, compiler executable, JDK17 and held
source are required. Its native result must be reviewed before any new pass claim.

Focused receipt-tooling checks12/12 and actionlint passed locally. Adding the
workflow guard produced an overall **13-method failure (12pass/1fail)** because
its substring check confused `overwrite-settings:false` with a write permission.
The owning token-line check was corrected; **only that failed method reran1/1**,
reusing12 unchanged successes. See [tooling review](macos-domain-tooling/review.json).
These are zero native executions. The extracted shared128-iteration array helper
additionally passes **one real Linux/JDK17 method**, exit0/2s/838held dirty inputs;
the four unchanged Linux methods and Compose were not replayed. See
[local helper receipt](macos-domain-tooling/linux-array-helper/receipt.json).
macOS code cannot be typechecked/executed by that Linux run.
The archival wrapper/array comparison error
failed before any ledger write and was corrected with original remaining bytes
checked; see [the tooling note](archive-tooling-note.json). No GitHub mutation
was repeated by that documentation repair.

## State and limitations

[Fresh remote readback](remote-after-closure/review.json): **64closed/108open/172**,
unchanged main`94d2492e`; ledger **47implemented/49partial/61verified/7unresolved**.
**IO-023/#58, IO-017/#53 and IO-018/#54 remain open**, as do independent physical/
minimum-platform, native parenting, full ABI/consumer/dependency/provenance/legal/
security/release gates. No packages, releases, deployment or Pages.

The [archive manifest](archive-manifest.json) lists126 explicitly selected public
JSON/XML/GitHub records. XML retains actual identities/counts/outcomes/messages;
console and stack bodies are omitted with original byte hashes. No raw Cargo,
portal or job logs, private data, ZIPs, binaries, credentials or environment dumps
are archived. Offline report review cannot re-execute absent native payloads.
