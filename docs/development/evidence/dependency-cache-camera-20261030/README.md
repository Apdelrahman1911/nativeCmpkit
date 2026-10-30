# Android camera receiver dependency-key omission — owning repair

`scripts/ci/dependency_cache_inputs.py:selected_inputs(libraries)` keyed geo,
sharing recipient/documents builds but not the independently assembled camera
receiver. Changing that receiver's plugin/repository/dependency declarations
could therefore reuse a cache under an incomplete recipe identity. This is a
**source-confirmed key omission**, not evidence of a corrupted cache or exploit.

Include only its fixed `PROJECT_FILES` with existing bounded, unshared, nonsymlink
hash guards. Actual repository keys now additionally bind the receiver's
`build.gradle.kts` and `settings.gradle.kts`. All previously selected declarations
remain unchanged in the isolated old/new selector comparison. Eight per-config
synthetic negatives and one symlink negative fail initially: **two methods / nine
failed subtest outcomes**. Focused dependency/selection/workflow guards then pass
**43/43 methods**, with held1064 inputs and Actionlint passing. These43 include
the repaired two; they are not45 unique tests or native/cache executions.

No outputs, APKs, keystores, XML, source files, copied test results or documentation
enter a dependency key/cache. Existing paths, read-only permissions, optional
SHA references and success-only cache save remain unchanged. **Failure-safe cache
saving is not implemented by this patch.** No timing improvement is claimed.
Current camera-restoration CI41100261882 is a separate older immutable input
scope and is not verification of this later selector change. BUILD-007/#40,
dependency locks/checksum provenance/native consumers/legal/security/release
remain open; no packages/releases/Pages/main/history change.
