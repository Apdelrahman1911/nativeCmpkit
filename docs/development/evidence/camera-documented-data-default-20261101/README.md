# Exact documented Android data default — source-only owning repair

Actual015 `41272457871` stays failed. Its original key/value/first conjunct/cause
remain unknown; the categories do not establish that it supplied `<temp>`.

The exact pair `disk.dataPartition.path=<temp>` is independently supported by
[pinned official hardware definitions](https://android.googlesource.com/platform/external/qemu/+/ae9d18d2b6261179fbd57fffec720a04f7bfb053/android/emu/avd/src/android/avd/hardware-properties.ini#847)
(lines847–859). The SDK CLI copies nonempty installed emulator hardware defaults;
see [AvdManagerCli](https://android.googlesource.com/platform/tools/base/+/45628254f0f8a9bb3755d73f3d30ca78fbb2153d/sdklib/src/main/java/com/android/sdklib/tool/AvdManagerCli.java#1074)
and the exact source/hash catalog in `source-review.json`.

For the unchanged fixed `-avd` launch (no `-data`/`-datadir`),
[main-common.c965–1015](https://android.googlesource.com/platform/external/qemu/+/ae9d18d2b6261179fbd57fffec720a04f7bfb053/android/android-emu/android/main-common.c#965)
overrides this config default with the AVD's `userdata-qemu.img` before creation.
The QEMU2 drive uses its `.qcow2` sibling. This is not a new supplied relative
filesystem path or externally retained temporary userdata destination in that
source contract; it is not an actual hosted runtime observation or binary-source
identity certification. Other emulator temporary-file behavior is not certified.

One exact new branch only. No config/launch rewrite, broad relative-path whitelist,
mutable/readonly/skin/parse/no-follow/FD/digest/liveness/cleanup/acceptance weakening.
`documented_data_partition_temp_default_observed=True` records only the current
parsed exact pair; absence makes no assertion and this Boolean never gates success.

The new positive synthetic regression first errors at original `require47`.
The candidate then passes exactly7/7 genuinely new methods/0skips/0.108924s,
seven distinct methods/eight executions total. The original red and new XML/JSON
are retained. Real exclusive synthetic FDs/Journal/digests/owned disposal and
near-match/traversal/foreign/readonly/nofollow/hardlink/tamper/live/unknown-transport/
unknown-child/no-retry controls are exercised. Removing only the new branch restores
the entire original helper AST; fixed launch AST and forward/inverse bytes hold.

SDK/AVD/emulator/build/compiler/native/dispatch0; accepted77/12 and all accepted
native suites not replayed. This is a narrow three-file private source freeze,
not a complete library/combined map. #13 remains open pending the sole remaining
Dont-keep actual retry and owning original-criteria/source/results/cleanup review.
All existing capacity/native/minimum/security/publishing/readiness gates remain.

Original XML has no terminal LF and is delivered through exact absent-only payload
mappings. The initial patch roundtrip refusal is retained in `packaging-refusal.json`;
no source or test was changed and no model was replayed to repair packaging.
