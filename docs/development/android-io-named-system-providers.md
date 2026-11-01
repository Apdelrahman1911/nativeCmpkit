# Android named system-provider verification

Issue [#55 / IO-019](https://github.com/Apdelrahman1911/nativeCmpkit/issues/55)
remains open. This fixture covers the missing **local named-provider** portion,
not cloud providers, minimum Android versions or packaged consumers.

## Exact scope

`android-io-named-system-providers` selects only two library methods in
`AndroidIoNamedSystemProviderTest`: ExternalStorageProvider and
DownloadStorageProvider. Both require the owned stock API35 emulator, user0,
English resources, a separate system-provider UID and no broad storage permission.
Existing controlled-provider/outage, IO, picker and Coil methods are excluded.

1. Insert one uniquely named MediaStore Downloads row in a fresh random folder.
   Record insertion ownership before writing; verify owner/name/path/ID before
   publication and each conditional deletion. Never recursively delete a tree.
2. Use an implicit `ACTION_OPEN_DOCUMENT_TREE` and genuine system UI/result.
   Accept only the requested authority and uniquely owned folder before metadata,
   reads or persistence. No injected URI, direct grant or privileged shell action.
3. Select the exact folder row inside `dir_list`; require the current toolbar
   title, source-bound PickFragment button, and exact caller/folder title **and**
   message in one refreshed active root before Allow. Ambiguous, stale or late
   observations refuse; acquired accessibility nodes and flag changes are owned.
4. Exercise public metadata, exact and oversized bounded reads, raw-source EOF
   and explicit close. Calibrate descriptor identity using the actual document
   URI, not an assumed MediaStore inode/mount mapping.
5. Persist/reopen/release the actual tree grant; require access denial, source
   survival and zero owned descriptors. Cleanup preserves the primary failure
   and deletes only the freshly identity-verified inserted row.

## Implementation and evidence boundaries

- `calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/` contains the
  two methods, nonexported caller and `NamedSystemDocumentsUi` ownership helper.
- `scripts/ci/android_io_named_system_documents.py` binds source and manifest
  admission. A source receipt explicitly cannot certify native/cloud behavior.
- Android15 DocumentsUI references: DirectoryFragment/ListDocumentHolder/
  GridDirectoryHolder bind `dir_list`/`android:id/title`; NavigationViewManager
  binds the toolbar title; PickFragment uses `android:id/button1`; ConfirmFragment
  formats `open_tree_dialog_title` and `open_tree_dialog_message` with caller first.
  Installed hierarchy/resource/MediaStore-indexing behavior still needs execution.
- Eight original source controls and18 new selector controls are qualified and
  reused without replay. Their synthetic success is not native success.
- Integration exposed a real strict reporter-manifest composition refusal in the
  old document helper. The [owning strict-union repair](evidence/current-platform-recovery-20261101/android-io-named-provider-owning103/README.md)
  admits only the complete old or complete qualified new shape, never partial
  hybrids. Twelve new and fourteen affected controls pass26/26 once; the fourteen
  earlier accepted controls are reused, not replayed.
- Actual reporter compilation passes0/38.522816s, not native execution. Its
  acquired signer warnings and inspection-custody limits remain documented;
  helper signing policy is unchanged and no security clearance is inferred.

Use the finite profile only after source admission and reporter compilation pass.
Reserve one hosted-heavy slot; globally at most two including queued/reserved jobs.
Cloud C1, API23–28, physical/vendor behavior and release/security gates remain.
