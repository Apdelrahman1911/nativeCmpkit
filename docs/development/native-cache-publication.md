# Native cache no-replace publication

## Confirmed Windows race, owning fix

Run40602393181 fails its existing picker concurrent reader/writer regression with
a Win32 sharing violation opening an already-returned cached payload. A late
writer that observed an absent target used `ATOMIC_MOVE`/replacement after another
writer returned that target. Java's atomic move is **not** a no-replace contract,
including when `REPLACE_EXISTING` is omitted (share's equivalent risk).

Both private extractors now stage/verify complete bytes and atomically insert a
hard link with `Files.createLink(target, complete)`. Existing matching winner is
verified/reused, never replaced; cache permission/owner/reparse checks remain.
Unsupported linking uses only its already verified private unique file, not a
replacing rename. Picker's differing owned payload is preserved with a unique
verified new payload; share's corrupt digest entry still fails closed. The old
three-argument JVM descriptors, public Calf/JNI/resource identities and notices
remain unchanged. No library rewrite or release is involved.

## Important executed tests

[Held-source Linux pass](evidence/cache-publication-20261027/green/receipt.json):
**29/29**, JDK17/Kotlin2.4.20/JUnit4/real filesystem/dependencies, zero skips.
Sixteen picker/thirteen share cache methods, four new. Seven source/test files and
738 selected inputs unchanged during execution; later Android fixture edits are
outside the seven compiled cache inputs.

[Two exact replacing-publication controls](evidence/cache-publication-20261027/replacing-control/receipt.json)
**both fail** before the owning no-replace policy passes. A late publisher is
paused with complete real staging; another publisher returns the target and a
real FileInputStream holds it open. The loser must return the same winner, retain
filesystem identity/bytes and remove owned staging. Both modules exercise real
IOException/unsupported-link private fallback without creating a target identity.
Existing ACL/symlink/alias/concurrent-byte checks remain. The one existing picker
replacement expectation is deliberately changed to assert old-byte preservation;
no historical failed record or acceptance criterion is deleted.

This is narrow Linux runtime, not packaged JNI/multi-process/Windows/macOS native
certification. **IO-022/#149 and NATIVE-031 stay open/partial.** Run the changed
Windows cache/JNI scope once; do not replay already successful unrelated save/share
policy jobs. Original loaded-DLL/multi-process/read-only/noexec/native-service,
provenance/legal/ABI/consumer/release requirements remain. No publication.
