# Private Apple help diagnostic proposal

Actual41254296009 remains **failed**, helper2/5.47s. Its complete help Result is exit0/stop_reason null/stdout0/stderr100; no raw text survives by design. Existing metadata cannot distinguish strict UTF-8 refusal from a mismatch in the single accepted Usage list. This proposal closes that evidence gap only. It does not interpret the existing digest, infer current SDK support or alter acceptance.

Only `help_observation`, two diagnostic constant declarations, and eight new test methods in a separate class change. Every other helper function/class and both existing test class bodies are AST-identical to the frozen preimage at100d43ca0e7c5049631002e2bf6a2db49d4c2573. Source/test paths and the exact four SOURCE_INPUTS remain.

The existing `syntax` literal, exact Usage regex and `usages == [syntax]` predicate remain unchanged. Valid-control requirements, original defaults and positive assignments also remain. Diagnostic normalization never feeds the predicate. A recognized alternate template or normalized rendering can still return unavailable. All command/15s/128KiB/90s/512KiB/owned wait/one-stop/partial-refusal/private-cleanup/five-minute/read-only/receipt-only gates remain unchanged. No library build, simulator inventory, payload query, boot/install/launch/signing or profile command is added.

New receipt fields are finite or bounded:

- `refusal_reason`: invalid-control-result, nonzero-help-exit, utf8-decoding-refused, missing-exact-usage-line, ambiguous-exact-usage-lines, unrecognized-exact-usage-syntax, or null for existing exact acceptance.
- `usage_line_count` and `strict_usage_line_count`: null before valid zero-exit decoding, otherwise capped at8. Candidate discovery permits only ASCII case and indentation around the fixed usage prefix; the strict count uses the untouched acceptance regex.
- `usage_lines_sha256`: SHA256 of at most8 complete diagnostic candidate lines, each capped at4096 UTF-8 bytes, framed by four-byte big-endian byte lengths. `usage_lines_truncated` marks either limit. No candidate text is serialized.
- `usage_prefix_observation`: only exact, indented, other-case or null. It is populated for one nontruncated candidate only.
- `usage_template_observation`: one literal from an explicit four-template allowlist, or null. The existing template and three alternate diagnostic templates are observations only, not statements about actual SDK syntax. Unknown tokens, arguments and paths never appear.
- `usage_template_normalized`: a boolean showing ASCII body whitespace/case normalization was needed for an allowlisted observation. This is diagnostic only.

The allowlist is exactly:

```text
simctl appinfo <device> <app bundle identifier>
simctl appinfo <device> <app>
simctl appinfo <device> <bundle identifier>
appinfo <device> <app bundle identifier>
```

**Eight new methods initially red**, all due to absent diagnostics; the immutable original red log/record and additive classification remain. There are21 error blocks because subtests share those8 methods, not21 methods. After the private correction: **8/8 pass, zero errors/failures/skips, exit0 /0.16106s** (unittest0.019s). Popen is explicitly forbidden by every new model. One collect model uses an injected fixed control plus owned temporary files and confirms receipt-only output/private cleanup. No accepted model, real child, SDK, app, library build/test or CI request was replayed.

**22 static review checks pass**, including exact acceptance and default assignments, unchanged owning transport/cleanup code and original test bodies, explicit diagnostic bounds, held source identities and a successful read-only `git apply --check` against exact private original files. The actual public-safe archive is unchanged. Raw synthetic logs stay private; patch/tests contain only explicit synthetic sentinels.

The two-file patch and exact postimages are reviewable now. Only the lead may integrate or select a later unchanged help-only request. It must establish its own frozen source identity and actual results. These models do not prove current help support, Darwin recovery, appinfo payload schema or profile/leaks. **#141/UI-038 and all original native/profile/leaks/GC and publishing/Pages/main/history/security/readiness gates stay open.**
