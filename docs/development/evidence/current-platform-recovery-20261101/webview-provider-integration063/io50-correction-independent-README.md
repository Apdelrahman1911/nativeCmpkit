# IO-013 / #50 — independent acknowledgement review

**Correction002 is source/integration-qualified only.** No compiler/native acceptance
or issue closure. The original sealed proposal remains preserved and causally refused.

Original manifest: `85cba7b0e1be1cf730307ccdf2dd30965c981e3907b366429f5320ef7265c159`.
Corrected manifest: `59de6632ba76a6dea3c5757bae6155465340ff4d6dbe137f8817b7d480661e2d`.
Corrected candidate: `d3732fd73cc98ec6cec1db3a694e4f1c8654c8146825b6339bee6a16fb404acf`.

## Causal correction

The original waiter could accept a client callback caused by native cancellation
*before* deliberately completing the held producer. A zero-counter gate alone also
has a race. Correction002 serializes entry, exit and that zero/one-arm boundary
with one existing NSLock. It retains a new nonce-bearing native NSError, discloses
it only through the actual held producer completion, and counts a matched exit
only for exact native object identity of the actual Foundation callback error.
The existing helper refuses nil/nil, compares native pointers rather than wrapper
or value equality, and keeps both references alive during comparison.

An already-entered callback refuses the arm. A racing earlier callback cannot
possess the retained error. Wrapping, copying, suppression or a foreign error
cannot satisfy the matched-exit gate. No unwrapping, equality or silence fallback
is allowed. The library callback runs outside the witness lock; native progress
and actual callback URL/error are forwarded unchanged.

## Verification and integration

- Independently verified 12 original and 13 corrected payloads and exact checksum
  membership; 29 selected repository/evidence identities and two cached dumps held.
- The four-hunk correction applies and inverts exactly. The full corrected addition
  produces exactly one 23,324-byte / 444-line / one-method file from the live absent
  preimage and inverts to absence. Public cancellation/resource assertions,
  registered native copy/progress and transactional fixture cleanup are unchanged.
- Six fresh abstract checks pass in 0.012176s, including the retained original and
  zero-only false-positive witnesses. One bounded property examines 1,405
  lock-ordered traces / 10,928 observed prefixes. These are not native executions,
  Foundation timing/identity guarantees, future-callback proofs, or additive
  coverage over prior author models. Author checks and accepted suites were not rerun.
- Cached declarations are Kotlin/Native 2.4.10; configured source selects 2.4.20.
  Typed overrides, definite assignment, actual Map bridging and native error
  forwarding still require the configured compiler/runtime.

Use **correction002 `addition.patch`**, not the original candidate or a delta
against a nonexistent live file. Lead must recheck preimages, resolve/compile the
existing `application.linkTaskProvider`, register only the suggested new one-method
selection and freeze complete native/build inputs before dispatch. See
`INTEGRATION_PREIMAGES.json` and `ONE_METHOD_PLAN.json`. The adapter XML names in
the plan are expected, not observed. Original XML, source/native behavior and
owned cleanup must be reviewed before acceptance.

Only C3, **“Cancel during provider copy,”** remains; C1/C2/C4/C5/C6 are reused.
Controlled typed result arrival and OwnProcess opaque image bytes are disclosed.
No Photos/cloud/extension, decoder, late-successful-URL, OS-purge execution or #52
scope is added. #50 remains open. No production/live/Git/GitHub/network/build/native
mutation or execution occurred. Full metadata dumps, machine paths and private
transcripts are excluded from this review packet.
