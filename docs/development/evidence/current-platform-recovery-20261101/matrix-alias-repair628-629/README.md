# Shared Calendar/Share matrix alias repair — originals628 / repair629

The two immutable requests at `7d6b6d5b43f93ae085dc66a3377b3c7967400bf7`
remain **FAILED before platform preparation**:

| Original request | CI source controls | Result | Platform/library execution |
| --- | --- | --- | --- |
| [CameraC1 41771597113](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41771597113) | 2,888 reported / five errors / 204.346 s | Failed | None |
| [Share AppKit8/JNI3 41771623474](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41771623474) | 2,883 passed / five errors / 200.056 s | Failed | None |

Each designated reviewer acquired its eight original log members **once** and
observed zero artifacts. Seven skipped zero-step downstream placeholders are not
executed platform jobs. The retained [Camera review](camera-original628-review.json)
and [Share review](share-original628-review.json) bind the actual failure, original
issue criteria and source provenance. Frozen Git source hashes are **not actual
native before/after maps**.

## Confirmed shared causes and owning repair

`workflow_matrix.py` gained `calendar_native.PROFILE` and
`macos_share_native.PROFILE` keys, plus their `MODULE` values and matrix branches.
Two older readers still assumed every unrelated declaration was a literal:

- `test_android_permission_demo_call_denial_recovery.py::matrix_environment`:
  three methods raised `NameError` because neither new alias was supplied.
- `test_android_permission_demo_denial_absence.py::validate_denial_route`:
  two methods rejected the new `ast.Attribute` keys/module values.

The shared `native_matrix_declarative_aliases.py` reads **only the exact literal
PROFILE/MODULE/FOCUS declarations of the two known source helpers**. It verifies
their import identities and does not import or execute native controller bodies.
Unknown aliases/attributes, nested accesses, dynamic expressions, drifted or
duplicate imports/declarations/keys and reassignment refuse. Literal-only mapping
evaluation and the exact original all-slot generator stay strict. Both old
readers use this same finite source-backed interpretation; no selector/workflow,
native/public API, dependency, historical source pin or Android assertion changes.

## Important test evidence

Only the **five failed old methods plus eight new ingress regressions** executed:
**13/13 passed once**, unittest **2.361 s**, wrapper **2.500129571883008 s**.
All **1,373 selected inputs** held before/after. The 17 original test bodies in
both old files are AST-identical; the unexecuted accepted methods were not replayed.
See [first result](first.json), [original assertions](original-assertion-custody.json)
and [lead source/results review](lead-source-results-review.json).

This is **zero SDK/Gradle/compiler/browser/native/library executions**, not a
Camera restoration or AppKit/JNI pass. The exact dated geometry recovery remains
SHA256 `175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4`.
The initial atomic patch rejected a wrong import anchor before changes; no source
or test failure was hidden. Every original native failure and release/security,
consumer/ABI/legal/dependency gate remains. **No issue closes in this repair**;
only the still-missing native populations may follow reviewed development push.
