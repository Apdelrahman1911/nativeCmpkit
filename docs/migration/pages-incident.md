# Unintended legacy GitHub Pages deployment

## Observed event and scope

During the migration, GitHub recorded a successful `github-pages[bot]` deployment
from the imported **historical `gh-pages` branch** at `2026-10-24T14:58:51Z`.
The deployment ID is **7300258890** and its commit is
`2c3055c523ed6efe183d828b7a7942d357cd4d29`. It was discovered during the final
repository-control inspection; no migration command requested a Pages build or
deployment. The exact internal activation mechanism is not proven. The observed
Pages configuration used `build_type: legacy` and the preserved branch as source.

This is an **unintended deployment**, not a nativeCmpkit release or a successful
deployment of the new documentation. Earlier blanket wording that no deployment
occurred was too broad and is corrected here. No release or package was published.
The deployment status is confirmed; public URL contents/reachability were not
tested. The API advertised a route under the account's Pages domain, which this
migration did not configure or change.

## Containment and unresolved administrative step

- Preserved the original branch object ID; **no history or branch was deleted**.
- Archived the Pages configuration, deployment and status history before changing
  repository controls. See the [machine-readable incident record](pages-incident.json).
- Disabled Actions between supervised verification runs. A minimal
  `enabled=false` API update succeeded after a combined policy update failed.
- Switched Pages from `legacy` to **`workflow`**, which disables legacy
  branch-triggered publishing. Current workflows have read-only token permissions,
  SHA-pinned actions and no Pages deployment step.
- GitHub rejected **three** `DELETE /pages` requests with HTTP422,
  `Deactivating GitHub pages for this repository is not allowed.` This persisted
  after switching publishing mode and using the current documented API version.
  Those are definitive API refusals, not uncertain requests that were blindly retried.
- **Existing deployment unpublishing is not verified.** The owner was asked to
  choose **Unpublish site** in
  [Settings → Pages](https://github.com/Apdelrahman1911/nativeCmpkit/settings/pages),
  without deleting `gh-pages`. No owner response or completed action is assumed.

The unresolved administrative action is tracked in
[issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171), assigned to
the owner. Its [creation/readback receipt](pages-followup-issue.json) records the
exact body and new issue metadata. This **Medium operational incident** is separate
from the 164 baseline findings and 170 managed audit/history issues; creating an
issue is not evidence that unpublishing occurred.
The [final read-only issue check](pages-followup-verification.json) likewise checks
identity, body, classification and assignment, not whether Pages was unpublished.

GitHub documents [unpublishing](https://docs.github.com/en/pages/getting-started-with-github-pages/unpublishing-a-github-pages-site)
as distinct from deleting a Pages configuration: it removes the current deployment
without affecting repository settings/content. The public REST API exposes a
[delete-site operation](https://docs.github.com/en/rest/pages/pages#delete-a-github-pages-site),
which did not work for this repository. Do not invent an unsupported bypass or
remove preserved history merely to make a control check pass.

## Verification policy and lessons

`verify_migration.py --remote` checks that any remaining Pages configuration is
in workflow mode, that no undisclosed deployments were created, that Actions are
disabled at handoff and that the original `gh-pages` ref is unchanged. It reports
the unverified administrative follow-up separately; a passing Git/archive integrity
check does **not** mean the existing site has been unpublished.

Future migrations must inspect Pages independently of Actions. Preserving a
publishing branch is not the same as authorizing it to be served. Recheck these
controls after imports/pushes and preserve the incident/deployment evidence even
after successful cleanup. Never describe this migration as having had zero
deployments, and never rewrite history to conceal the incident.

Evidence is under `docs/testing/evidence/github-actions/`, with exact filenames in
`pages-incident.json`. Later verified containment should be appended as a dated
resolution, not substituted for the recorded failures.

## Verified owner resolution — 2026-10-24, development phase

The owner reported completing **Unpublish site**. A subsequent authenticated
Pages API read succeeded and returned `status: null` with `build_type: workflow`.
The canonical GitHub Pages URL and both HTTP/HTTPS forms of the API-advertised
custom-domain route returned **HTTP 404**. The original `gh-pages` object remains
`2c3055c523ed6efe183d828b7a7942d357cd4d29`; Actions were still disabled.

These independent observations verify the requested unpublishing at the recorded
time. [Resolution receipt and checks](../development/evidence/pages-unpublishing/verification.json)
link hashed API and public HTTP observations. The historical deployment still has
a `success` status, and the Pages configuration still exists: neither is evidence
that the site is currently published. No history, DNS or account-domain settings
were changed. HTTP observations are not a guarantee about every CDN cache.

The unresolved wording above and the original `false` fields in the incident JSON
are retained as the migration-time record, superseded by its additive `resolution`
section. Issue #171 may now be closed with this evidence; subsequent library
verification/publication does **not** authorize another Pages deployment.
