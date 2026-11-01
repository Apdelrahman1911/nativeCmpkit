# NAV fixture identity recovery

Exactly six methods in the lead's original 17-method batch failed at the real
ArtifactVerifier unknown-module guard. The 21-entry identity describes declared
publication roots; NAV is an unpublished experiment and calf-navigation does not
apply publication. Nothing in this recovery makes it a publication root.

The two-file proposal changes the synthetic test helper and the new developer
document. NAV alone receives an appended fixture identity row via unittest.mock
while the constructor reads identity.json. That row is explicitly marked
synthetic-fixture-only. The actual canonical identity is parsed outside the mock;
the mock must receive those exact identity bytes exactly once and is removed
before archive inspection or runner POM/module parsing. UI/Core fixtures retain
the existing direct constructor path. All live verifier checks stay byte-identical.
A new guard proves the exact 21 default roots, NAV/unknown rejection before and
after the synthetic constructor, restored parser identity, and unchanged on-disk
identity bytes. No new constructor parameter or public/module acceptance is added.

The new developer document now stages and inspects only UI's existing producers.
The NAV map is an explicitly synthetic future archive policy plus current local
source retention; it has no actual NAV binary, Maven coordinate or producer
acceptance. All seven UI intended target shapes and source/primary/companion
families remain required. Actual Apple outputs still need a supported producer.

Exactly the six failed methods plus one new guard pass 7/7 in this private copy:
unittest 0.639s, subprocess 0.796202s, exit 0, no skips. The original 17-method
failed log (6 errors, 1.072s) and receipt remain byte-identical and are copied under
original-red. All 13 original authored method bodies remain AST-identical; the
four source/license/Git methods and seven other previously accepted methods were
not rerun. Thirty-eight selected source/notice/identity/checker inputs held during
the run; all live selected bytes are unchanged. Read-only git apply --check passes.

The source/license/Git controls from the lead's first batch are reused only after
exact input and method-body review. The six methods' existing source/header/body,
wrong-path, module notice, target applicability, full companion, exact-coordinate,
omitted-sources metadata, and no-payload-mutation assertions are preserved.
The extra guard adds identity-scope evidence without weakening archive checks.

This verifies Python fixtures using authored ZIPs, not real compiled JAR/AAR/KLIB
objects, packaged consumers, runtime/native behavior or legal/release readiness.
UI actual source/primary/companion retention remains pending for its real producer
outputs. NAV future binary distribution remains unobserved and synthetic policy
results are not future publication compliance. The original four #103 criteria
are preserved; no issue closure or publishing/GitHub operation was performed.
