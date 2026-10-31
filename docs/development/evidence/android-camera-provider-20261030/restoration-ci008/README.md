# Camera restoration008 — tooling failed; zero native work

[41240921685](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41240921685),
attempt1, immutable5e9cfdd1126ba535475f920bdbba827d72eed535, **FAILURE**.
CI1190 synthetic methods/1189pass/one stale saver-serial assertion,67.272s;
earlier35/80/84 groups pass but are not native library tests. All downstream jobs
skip: zero native/cache-action/XML/artifacts. Exact994/1071 Git inputs verified.

The failing source is `test_desktop_saver_state_focus.py:149`, requiring saver to
be the last serial OR term. Workflow:228 correctly retains saver serial1 and adds
the browser profile; default2 is unchanged. `request/` and `independent-review/`
preserve exact selection, state, source/log hashes and public metadata. Original
tooling log remains private, not stripped/reclassified into a native pass.

[Owning correction](../../serial-profile-guard-recovery-20261031/README.md) changes
only the guard. Flags3 fixture still has zero native executions; cumulative
restoration20/zero accepted. #13 remains open; original rotation's immediate
in-held recreation timing and possible disappearing-task conservative refusal
remain separate source limitations, not this observed tooling cause.
