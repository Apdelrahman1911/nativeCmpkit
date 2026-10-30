# Exact manifest/runtime/handler ownership repair

Two important synthetic guards first fail: the stale diagnostic wording guard
from [actual41100261882](../restoration-ci002/README.md), and a newly authored guard
for a **separate source-confirmed fixture defect**. Android15's reviewed
[public source chain](public-component-state-source.json) sets `ActivityInfo.enabled`
from the parsed manifest. User component override is used for selection, not that
flag. Comparing disabled-default manifest `enabled` to `armed=true` would reject
a correctly enabled component. This was **not reached** by recovery002 and is not
its cause, nor a retrospective cause of the earlier empty CLI reply.

Keep the manifest disabled and originalDEFAULT lease, verify the actual component
setting, then require real package-scoped implicit IMAGE_CAPTURE resolution:
**one exact own-UID/component when armed, zero when restored**. Unknown/null/
foreign/unexpected handlers fail, as do missing Bundle readback fields. All nonce/
UID/signature/main-Looper/SDK35/DONT_KILL_APP/native process checks and restoration
before binding close remain. No manifest patch, fake effective flag, root,
arbitrary RPC, manual grant or silent fallback is added.

The stale guard now checks `protocolError` and all unknown/live/failed-complete
branches, not diagnostic prose. **52/52 important synthetic methods** pass; after
adding reporter field-presence assertions, **five overlapping component methods**
pass on the later exact input snapshot. Not57 distinct functions. Actionlint
passes; accepted1121 earlier methods are not replayed wholesale locally.
Final bounded serial compilation passes reporter0/37.01s and receiver0/14.0s with
**987 library/1064 combined inputs held**, zero native executions. Receiver is
actually recompiled because its native source changed, not reused incorrectly.

#13 remains implemented/open until its four still-unverified API35 methods and
all three original criteria pass on immutable source. Provider#78/IO precheck/
host results remain separately accepted and are not replayed. Physical camera,
minimum/vendor/heap/consumer/ABI/dependency/legal/security/release, publishing/
Pages/main/history and solo/8GiB/max-two-heavy requirements remain.
