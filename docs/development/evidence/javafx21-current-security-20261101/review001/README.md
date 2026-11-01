# Current JavaFX21 dependency review — 2026-11-01

See [PUBLIC_REVIEW.md](PUBLIC_REVIEW.md) for the source/advisory analysis and
[LEAD_NEXT_VERIFICATION.md](LEAD_NEXT_VERIFICATION.md) for literal remaining tests.
The existing21.0.13 pin is already the highest stable21 in the observed metadata;
no version-only change is justified. Eight new metadata models were accepted,
not rerun by the lead. Historical30 artifact/ten sampled classfile observations
are reused, not new runtime or patched-engine/security acceptance. #144 stays open.

The lead checked every sealed member checksum and excluded private paths; no
packages/native binaries were imported, tested, installed or published here.
