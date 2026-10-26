# Controlled dependency fixtures: preserved execution evidence

These are **plugin-free local Maven fixtures**, not nativeCmpkit dependency
acquisition, independent provenance, library tests or release gates. Ordinary
root/convention policy remains uninstalled. No publication or remote mutation
occurred. Commands, Gradle/JVM identity, input/tool hashes and individual results
are recorded per invocation; original failures are not overwritten.

| Batch | Actually executed | Outcome |
| --- | --- | --- |
| `fixture001` | One bootstrap;8.55s suite | Init compiled on Gradle9.7.1/JDK17.0.20. Project graph resolved, but an unmodeled script-root identity failed the aggregate. XML was emitted, no project lock finalized. Zero positive/negative checks. |
| `fixture002` | Bootstrap, ordinary baseline, wrong JAR SHA, strict transitive drift;34.76s | Bootstrap/baseline exit0; exact wrong-checksum rejection exit1 as expected. Drift exit1 contained actual typed lock conflict, but the original matcher did not recognize its wording, so original suite exit1/unverified drift is retained. |

## Archive layout and integrity

Each batch has `archive-manifest.json`, mapping original relative source paths and
hashes to archived paths/hashes. Candidate markers bind generated settings/builds,
repository input bytes and the six frozen tool inputs. `tool-inputs/` preserves
those exact pre-run helper versions for reproducibility; they are historical
evidence, not current instructions or policy to execute automatically.

- Invocation and owner/build graph JSON are copied byte-for-byte, including each
  configuration's exact failure/selected components and false coverage flags.
- Finalized verification XML and available project lockfiles are exact copies,
  both in captured invocation state and candidate-relative locations.
- `initial-verification-metadata.reconstituted.xml` is explicitly **reconstituted**
  from the deterministic fixture generator only after matching the original
  pre-invocation receipt SHA256. It is not mislabeled as a recovered original file.
- Logs replace only the known task workspace/installed Gradle paths. Manifests
  retain hashes of both original and sanitized text. The checksum HTML is preserved
  as plain `.html.txt`; referenced JavaScript/CSS/image assets are not copied or run.
- Local Maven JARs and caches are not copied. Their exact hashes/sizes and harmless
  deterministic generation source are retained. POM/repository XML inputs are exact.
- No environment dumps, credentials, private machine files or daemon logs are included.

## Structured observation of fixture002 drift

`fixture002/posthoc-constraint-observation.json` is additive read-only analysis,
not a new Gradle invocation or a rewritten original result. The repaired observer
requires all of:

1. Parent→leaf `[1.0,2.0)`, root locked-leaf `{strictly 1.0}`, and root requested-leaf
   `{strictly 1.1}` unresolved edges in the exact project/configuration.
2. Actual `ModuleVersionResolveException` and `ConflictingConstraintsException`
   cause types, with the exact `1.0 - from lock file` and1.1 conflict requirements.
3. The exact parent1.0/leaf1.0 lock set and known JAR+POM trust/bytes for both leaf
   versions, with source/verification/lock state unchanged.
4. No checksum error or unrelated configuration/artifact failure explaining the exit.

The repaired parser has offline positive/negative regression tests; a fresh003
bootstrap/baseline/drift sequence is the next scheduled runtime check. Other
authored fixtures, mutable dependencies, script locking, actual root/convention
graphs and every required host remain separate gates.
