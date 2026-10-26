# Hash-locked local documentation environment

These locks cover **Linux x64 / CPython 3.12** only. They are an explicitly
labeled **TOFU bootstrap** from official PyPI release metadata, not an independent
provenance/signature review. They do not authorize publication or Pages.

- `docs.in`: four direct, exact MkDocs/plugin requirements.
- `docs-linux-py312.lock`: 38 exact runtime packages and selected artifact SHA256s.
- `docs-build.in` / `docs-build.lock`: four exact wheel-only build tools; `packaging`
  overlaps the runtime graph, yielding 41 unique selected artifacts in total.
- `docs-lock-provenance.json`: exact public artifact URLs, hashes, roles, source
  timestamps and bound input hashes. Source-only `csscompressor` and `jsmin` use
  the pinned build backend; their generated wheel bytes are not claimed reproducible.

After coordinating local work and ensuring an 8 GiB disk reserve:

```sh
python3 -m unittest discover -s scripts/docs -p 'test_*.py' -v
python3 scripts/docs/verify_locked_environment.py \
  --output build/docs-verification/new-unique-run --build
```

The helper requires a **new** project-owned output directory, validates every
lock/provenance input, bounds official artifact downloads, checks SHA256 before
installation, creates a fresh isolated venv, and installs only from its local
wheelhouse with `--require-hashes --no-index --no-cache-dir`. Source builds use
`--no-build-isolation` plus the already hash-verified pinned backend. Child
processes receive a minimal environment and private HOME/temp directories, not
arbitrary caller credentials/config. This is **not a security/network sandbox**;
the two source-package backends execute code after checksum verification.

It verifies all 41 installed versions exactly, runs `pip check`, proves a real
pip wrong-SHA rejection using a separate local fixture, optionally runs strict
MkDocs **build only**, and rejects lock changes during the run. Commands are
time-bounded and only their owned process groups are terminated. No deploy,
shared pip cache, global Python environment or existing docs venv is modified.

Updates are explicit, not an install-side repair: resolve and review a separate
isolated documentation graph, then use `scripts/docs/bootstrap_lock.py --write`
with that environment's Python. Review input/artifact changes and rerun the fresh
install/tamper/build checks. The bootstrap reads only named installed dependency
metadata and official release metadata; it does not freeze unrelated machine
packages. Never flip `independent_trust_reviewed` merely because downloads match.

Inspected run: `docs/development/evidence/build/docs-locked-002-receipt.json`.
Fresh installation, all versions, `pip check`, expected wrong-hash rejection and
strict local MkDocs build passed. The preceding stale historical-link build
failure is retained separately; neither run deployed a site.
