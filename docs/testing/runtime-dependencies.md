# Resolved desktop dependency and advisory audit

## Observed graph

The metadata-only Gradle export completed on Linux/JDK17/Gradle9.7.1 against the
migrated source at `3d2b772b27bed3da0f34677225b843d29f1c3ba6`:

- **25 `desktopRuntimeClasspath` configurations**, covering all 24 included
  library projects plus `sample:common`.
- **193 unique exact Maven coordinates**, 8,613 selected graph edges across the
  configurations, zero unresolved edges and zero resolution exceptions.
- Project/module identities, variant attributes and selection reasons retained.
- No runtime artifact bytes, Cargo task, publication or native GUI were requested.

See [the graph](evidence/desktop-runtime-graph.json),
[bounded command/result log](evidence/desktop-runtime-graph.log), and
[OSV receipt](evidence/desktop-runtime-security/osv-desktop-runtime-query.json).
The graph SHA256 is recorded in the advisory receipt.

**Scope matters:** this is not a complete project SBOM. It excludes Android,
Apple, browser, test, Gradle-plugin and native dependencies bundled inside JARs.
The desktop sample launcher uses `jvmRuntimeClasspath`, not the selected
configuration name, so its launcher-specific graph is also outside this export.
The direct catalog and separate Rust graph scans complement, not replace, these
gaps. Source/metadata availability is not a binary provenance certification.

## Advisory result

OSV answered all **193** exact-version queries. The sole match was
`org.openjfx:javafx-media:19` → **GHSA-47g3-mf24-6559 / CVE-2024-20925**, the same
Low-severity match previously found in the direct catalog scan. The archived
advisory classifies it Low and gives
`CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N`.
No exploitation, reachability or consumer impact was demonstrated. Query replies
contained no pagination tokens. A zero match for another coordinate is not proof
that its transitive/native payload is vulnerability-free.

## Reproduction and exporter correction

```sh
./gradlew --init-script scripts/audit/export_desktop_runtime_graph.init.gradle \
  --no-configuration-cache --max-workers=2 \
  '-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8' \
  auditDesktopRuntimeGraph \
  -PauditDesktopRuntimeGraphOutput=build/audit-desktop-runtime-graph.json \
  -PauditRevision="$(git rev-parse HEAD)"

python3 scripts/audit/scan_runtime_osv.py \
  --graph build/audit-desktop-runtime-graph.json \
  --output-dir /tmp/nativecmpkit-runtime-security
```

The first exporter attempted cross-project resolution from one root task. Gradle9
rejected every configuration with `IllegalResolutionException` before dependency
resolution. The failed script, graph and log are retained under
`evidence/desktop-runtime-graph-cross-project-failure*`; this was an **audit-tool
defect**, not a library dependency failure. The corrected exporter resolves in
each owning project's task and only aggregates JSON at the root. Its subsequent
97-second run succeeded. Each snapshot runs freshly; unresolved selectors/error
types are retained and make the aggregate fail instead of claiming completeness.

The OSV helper sends only public package identities/versions and retains exact
queries/results plus matched advisories. Its seven offline fixtures test schema,
identity validation, deduplication, batch alignment and API-response shape. A
future reply requiring pagination is rejected rather than reported complete;
explicit per-package follow-up would then be required.
No automatic severity assignment, dependency upgrade or exploit testing occurs.
