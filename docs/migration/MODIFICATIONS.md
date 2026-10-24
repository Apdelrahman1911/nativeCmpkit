# Migration modification record

Migration date: **2026-10-24 UTC**. Original baseline:
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. See appended Git commits for exact
changed files and authorship. No historical commit was rewritten and no upstream
repository object or setting was modified.

## Changes made

- Independent repository identity, root project name, prospective Maven group,
  publication artifact mapping / POM metadata, development version and sample
  names / application IDs / signing-team ownership.
- Explicitly retained public namespaces, Android generated namespaces, Compose
  resource package, JNI symbols, native library paths and project accessors.
- Vendor-neutral installed JDK 17 daemon selection, replacing the upstream vendor
  and platform-specific provisioner URLs after observing a portability failure.
- Read-only CI definitions with action SHA pins; removed active auto-publishing,
  Netlify and Pages deployment workflows. Originals are archived intact. All
  repository Actions remain disabled. Added a Maven repository task opt-in
  interlock; it is not a substitute for explicit owner authorization.
- New README / installation / maintainer knowledge base; inherited feature guides
  now mark unpublished coordinates and historical claims. Original README,
  installation, homepage, docs config, conduct policies and workflows are available
  under `legacy/` as well as their unmodified historical commits.
- Retained Apache LICENSE and original copyright. Added NOTICE / third-party
  license texts and provenance; changed files carry migration comments where the
  format permits. Updated project contact references; private vulnerability
  reporting is enabled. No private owner email or signing identity is invented.
- Added reproducible GitHub metadata export, SHA256 manifests, Git bundles, audit
  inventories / findings / evidence, characterization probes, review procedures,
  roadmap and issue-creation tooling. These are not a guarantee of correctness.

## Deliberately not changed

Public `com.mohamedrejeb.calf.*` APIs and runtime behavior remain based on upstream;
no major architectural rewrite or broad dependency upgrade occurred. Identified
functional, performance and security issues are documented for follow-up, not
silently marked fixed. Experimental/stub modules are not promoted to supported
features. Original `v0.*` tags and preserved non-main branches are historical Calf
refs, not a newly validated nativeCmpkit release line. Historical release records
are archived only; no release or package was published.

## Independence and limitations

The Git bundle, preserved branches/tags, source, docs and metadata archives are
self-contained with respect to the original repository. External build dependency
registries and platform SDKs remain necessary. Links to upstream are citations,
not build/download requirements. Deleted/private/redacted objects cannot be
restored; inaccessible APIs and attachments are recorded explicitly in
`metadata-coverage.md`. See `verification.json` and `docs/testing/` for checks
actually performed, not merely planned commands.
