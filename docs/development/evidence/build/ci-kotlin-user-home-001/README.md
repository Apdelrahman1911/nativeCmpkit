# Optional explicit Kotlin user home: contained helper correction

The lead authorized only `scripts/ci/library_tests.py`, its tests and this
additive evidence. The new optional `run --kotlin-user-home` is browser-only
(JS/Wasm), repository-relative and strictly below root `build/`. Existing
path-component symlinks, traversal, external/root paths and non-directory
components reject before output/quarantine/execution. Prepared nonempty homes
are retained; their contents are not recursively certified or isolated.

The canonical path is exactly one `-Pkotlin.user.home=...` argument in both
execution and the existing recorded command. No arbitrary Gradle-argument
channel, default-command change, report-gate replacement or success relaxation
was added. The original run body is AST-identical after removing only the new
command-call keywords and optional parameter; all30 old test-method/fixture
ASTs and six other CI source files are unchanged.

Actual offline results: baseline51 passed; the11 newly added tests against the
old helper failed with34 subtest errors (missing optional interface); corrected
focused11 and complete62 passed. Logs and exact commands are retained. Synthetic
run tests mock runtime capture, Git and process execution but use the real
source snapshot/report parsing/receipt gates. These are **not browser tests**.
The direct CLI `--help` command also passed without runtime capture or Gradle.

The lead's earlier full Wasm run's environment-only home request did not bind
its generated Karma configuration; the cause remains unknown. Its failure is
not rewritten here. A previously successful explicit `-P` cold installation
is separate evidence. This option records **requested context only**, not KGP
effective use, generated-config paths, script suppression, package integrity,
independent trust, a browser pass or release readiness. Those require separate
inspected runtime evidence. No prepared real tooling home was modified here.

Future use, only in a newly authorized/source-frozen browser slot, can request
`--kotlin-user-home build/wasm-tooling-runtime-001/kotlin-user-home` with the
normal helper `run` options. This example was not executed by this correction.
The lead must still independently inspect generated configuration paths.

Read `checkpoint.json`, `static-review.json` and `archive-manifest.json`.
No Gradle/Java/Node/Yarn/browser/network invocation, issue change or publication
was performed in this correction. The nine core006/observer003 files remain
frozen. Independent helper review is a separate subsequent record.
