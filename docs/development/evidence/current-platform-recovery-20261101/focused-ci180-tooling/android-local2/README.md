# Android Local2 original review — run 41355429513

The [original run](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41355429513),
at `5539c0085dd8e1f3af4302026556aaa7bdabef96` on
`development/preview-hardening`, is **FAILED / ZERO new native executions / ZERO
XML**. Attempt1 finished at22:09:20 UTC on2026-11-01. The original metadata and
checkout log agree on the expected immutable revision.

Tooling failed before profile selection. `library-tests` and five other downstream
jobs were skipped. The lead requested `android-io-named-system-providers`, but the
original selection step never ran; no executed profile/focus is claimed. No
library Gradle invocation, API35 runtime, SELinux state, provider/grant/resource
observation or native cleanup receipt exists for this attempt. Artifact inventory
is zero. Native zero follows from the skipped job, independently of empty XML.

The original `scripts/ci` discovery reports **2275 tests /122.049s /20 failure
records / process1**. Those records belong to13 distinct tooling methods, including
repeated subtests. Earlier audit35, migration80 and development90 discovery stages
report OK; the overall tooling job is failed. These source controls are not native
library passes or newly accepted platform outcomes.

Eighteen records fail before their mutation because a required authored source
anchor is absent: one selector helper at line27 and17 refusal helpers at line29.
Two application/request subtests apply their mutation but receive the strict
`Application-specific DocumentsUI resource admission changed` refusal instead of
the older expected `Refusal-only DocumentsUI resource observations changed`.

Independent passive reading of the immutable source demonstrates the mechanism:
both legacy classes copy the current helper, then mutate it before `source_contract`
validates it. The current helper contains the complete new admission fragment once
and the old refusal fragment zero times. `source_contract` line231 first invokes
the mandatory complete-new-form guard at lines185–196. Neither failing boundary
demonstrates a native provider, resource or grant defect. The original failed
controls and their exact subtests remain in [failure-records.json](failure-records.json).

| Source file | Method | Failure records |
| --- | --- | ---: |
| `test_android_io_named_system_documents_ui.py:81` | `test_runtime_strings_cannot_be_resolved_in_the_id_namespace` | 1 |
| `test_android_io_named_system_resource_refusal.py:67` | `test_diagnostic_cannot_add_an_alternative_control_lookup` | 1 |
| `test_android_io_named_system_resource_refusal.py:91` | `test_diagnostic_getter_exception_cannot_replace_original_failure` | 1 |
| `test_android_io_named_system_resource_refusal.py:52` | `test_id_nonzero_and_exact_original_name_guard_cannot_be_weakened` | 1 |
| `test_android_io_named_system_resource_refusal.py:77` | `test_label_capture_cannot_move_before_existing_system_app_admission` | 1 |
| `test_android_io_named_system_resource_refusal.py:62` | `test_namespace_cannot_be_guessed_from_admitted_application_id` | 1 |
| `test_android_io_named_system_resource_refusal.py:108` | `test_namespace_categories_require_exact_package_delimiters` | 3 |
| `test_android_io_named_system_resource_refusal.py:72` | `test_observation_cannot_execute_before_the_original_lazy_refusal` | 1 |
| `test_android_io_named_system_resource_refusal.py:115` | `test_original_failure_message_prefixes_cannot_be_replaced` | 2 |
| `test_android_io_named_system_resource_refusal.py:82` | `test_raw_package_request_identifier_and_resource_names_cannot_be_exported` | 4 |
| `test_android_io_named_system_resource_refusal.py:100` | `test_short_circuited_name_comparison_cannot_be_reported_as_observed_or_true` | 2 |
| `test_android_io_named_system_resource_refusal.py:57` | `test_string_original_name_guard_cannot_be_weakened` | 1 |
| `test_android_io_named_system_resource_refusal.py:96` | `test_zero_identifier_cannot_enter_post_refusal_name_getter` | 1 |

The source declares only these two enabled native methods in
`AndroidIoNamedSystemProviderTest`, through the class filter and
`:calf-io:connectedAndroidDeviceTest`:

- `externalStorageProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership`
- `downloadsProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership`

Both remain **unexecuted**. Source retains genuine implicit tree selection, exact
native result/authority admission, uniquely owned MediaStore rows, metadata and
bounded reads, explicit descriptor ownership, persisted grant release and narrow
conditional cleanup. None of those assertions has an execution witness from this
attempt. The lead's1177-input expectation has no new hosted before/after map.
[Source bindings](source-binding.json) identify15 immutable Git snapshots used for
this passive review only.

The original log archive was acquired once and retained with SHA256
`de788a95b01ba86270a1cdfad21230b80a1fc453f84b8b1d320bde1136eae195`.
No artifact download was attempted because the original inventory is empty.
The reviewer ran no repository models, controls, compiler or native request and
made no live source/Git/GitHub changes. This report contains no private logs or
review-directory paths.

**#55/IO-019 remains open. Local2 and cloud-folder C1 still require their original
real execution criteria.** Source-qualified admission and the accepted Android
APK/compiler evidence remain separate. No readiness, publishing, Pages, main,
history, native, consumer, API-ABI, dependency, legal or security gate changes.
