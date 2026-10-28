# Packaged WebView consumer preparation — 2026-10-28

**BUILD-001 / [#1](https://github.com/Apdelrahman1911/nativeCmpkit/issues/1)
remains open. No packaged WebView test has executed in this checkpoint.**

The new independent [`webview-desktop`](../../../../tests/consumer/webview-desktop/README.md)
fixture stages only the WebView metadata/desktop publications, once per host,
then resolves/runs two public tests in each of two separate fresh consumer trees:
Gradle module metadata (root coordinate) and POM-only (explicit desktop
coordinate, with metadata redirection disabled). It never substitutes producer
classes/projects/internal owners or the existing sample. Runtime origin checks
bind the actual loaded JAR to held staging and its exact metadata display-name/
Maven-URL/hash mapping; POM resolution's canonical filename is recorded distinctly.

Public Compose WebView is mounted in a real Swing window/JFXPanel, loads Unicode
HTML, evaluates object/null/undefined/throwing JavaScript and releases its native
embedding owner. Tests fail on unavailable/headless/native conditions, rather
than using assumption skips. The consumer explicitly requests all six aligned
JavaFX21.0.13 host classifiers. The five-host matrix covers Linux x64/arm64,
macOS x64/arm64 and Windows x64, with bounded two-way concurrency and finite
failed-host recovery profiles. Verification permissions remain read-only.

## Actually inspected preparation outcomes

- `configuration001/`: offline Gradle configuration **FAILED** on uncached
  `error_prone_annotations:2.27.0`, exit1/14.00s, actual JDK17 and held inputs.
  No build-script or runtime pass follows.
- `configuration002/`: normal acquisition/configuration **PASS**, exit0/21.01s,
  actual JDK17 and held inputs. `help` executed; **zero Kotlin library/consumer
  runtime tests**. The pre-existing Core/IO staging directory was only a required
  directory parameter and was **not consumed or changed** by this configuration.
- `tooling001/`:16 methods, one error: duplicate XML correctly rejected by the
  existing parser, but the synthetic fixture expected a narrower exception.
  Original XML is now saved before parsing; invalid duplicates still fail closed.
- `tooling002/`:16/16 focused synthetic methods pass, not native/runtime tests.
- [40754502594](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40754502594),
  immutable `dacc5567`, **FAILED before any consumer job**. The577-method CI
  tooling suite had one old whole-workflow cache-count assertion expecting two
  keys; this new separately scoped producer adds the third exact key. No comma
  selector was put into a key. All consumer jobs were skipped, zero native tests.
  Initial dispatch visibility lag was reconciled read-only, not redispatched.
- `cache-recovery001/`:85 selected owning tooling methods pass with held834
  inputs on the dirty precommit repair. The exact three-key assertion and the
  no-raw-comma selector checks remain; no cache/input/consumer gate was relaxed.
  This85 includes the earlier16/45/9 selections; do not sum them as unique tests.

The original successful7-method Core/IO consumer is not replayed or generalized.
Old `build/verification-repo` is preserved. Candidate data in the known producer
cache group fails instead of being deleted/exported; separate child Gradle/HOME/
tmp are uncached. Only JSON/original XML evidence, not packages or private/full
job logs, is uploaded. No full21-root/API/ABI/minimum-platform/dependency trust/
legal/security/release gate is cleared. Cross-host generated dependency-selector
comparison and actual consumer runtime review are still required before #1 closes.
