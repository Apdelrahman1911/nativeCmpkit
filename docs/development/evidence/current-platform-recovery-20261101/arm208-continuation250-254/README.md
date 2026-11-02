# ARM208 fixture-family recovery — solo250–254

**Private source/discovery verification, not native ARM or packaged-consumer
acceptance.** The adapter is not integrated into the current repository. The
original208 remains failed; its13 completed cases and23 partial observations
are not replayed or relabeled as a fresh complete suite.

## Confirmed fixture cause and owning correction

CPython3.12.3 `unittest.mock.patch.object` can assign some metadata attributes
but tries to delete them during cleanup when they are not local dictionary
entries. A function's `__dict__`, and a type's `__name__`/`__qualname__`, are
assignable but not deletable. The original208 failed on function metadata cleanup.
The supplied repair correctly restored that dictionary by assignment in
`finally`, checking its original object identity and contents.

[Actual250](first-results250.json) then reached three selected cases: function
metadata and class documentation passed; **class-name cleanup raised TypeError**.
One method/three cases/Gradle-none/native-none, wrapper2.315037s. The checked
adapter result preceding that cleanup is not accepted as a passing case.

The solo owning repair also handles the related, still-unseen class-qualified-name
descriptor. For exactly those two identity descriptors on the exact known type:

```python
original = getattr(owner, name)
try:
    setattr(owner, name, value)
    yield
finally:
    setattr(owner, name, original)  # Never delattr a non-deletable descriptor.
    assert same_loaded_class_object
    assert getattr(owner, name) == original
```

The actual helper additionally checks exact `type`, descriptor-name allowlisting
and original string type. The previously accepted function-dictionary helper
remains byte-identical. Original G13 assertions, accepted two methods and four
T08 bodies remain; only finite failed/unseen selection and owning cleanup change.
The adapter and its16 private dependency images are unchanged.

## Important remaining-only results

- [Plan251](remaining-plan251.json) selects failed class-name1 plus36 unseen
  cases: five methods/37 cases. The two partial250 passes and original208
  completed13/partial23 are excluded.
- [Actual253](remaining-results253.json): **5/5 methods,37/37 cases pass**,
  zero errors/skips/expected failures. unittest14.785s; driver/wrapper clocks
  are separately recorded, wrapper15.219812s.
- Driver/control/lock/private inputs and profile/output leases hold; no fixture
  leftovers or forbidden events. Controller function-vector calls0; exactly one
  genuine new discovery-footer call. Accepted ownership8 bodies are not entered.
- T08 filesystem controls use real POSIX descriptors/files with explicitly
  controlled refusal/close failures. They do not test Kotlin/native library I/O.
- Solo252 source qualification60 passive checks and [review254](source-results-review254.json)
  13 passive source/result checks qualify this private continuation. Current
  **1203 library/1281 canonical combined** inputs hold; no live source edits,
  compiler, native, browser, ARM-host or consumer execution occurred.

No full original G13_3 or7/75 acceptance is inferred from these interrupted and
remaining-only populations. Exact current live-source composition/bindings must
qualify before adapter integration; do not replay unchanged accepted controls.
No issue closes or release gate advances. Continue solo, serial local/8GiB and
max2 combined hosted reservations including queued. All publishing/Pages/main/
history/native/consumer/API-ABI/dependency/legal/security/readiness gates remain.
