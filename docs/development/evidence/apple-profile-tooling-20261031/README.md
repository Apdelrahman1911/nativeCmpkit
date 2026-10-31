# Apple failed-profile request — tooling failed, Apple skipped

[41241378533](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41241378533),
attempt1, immutable5e9cfdd1126ba535475f920bdbba827d72eed535, **FAILURE**.
1190 CI synthetic methods/1189pass/one stale serial guard,66.840s. Earlier35/80/84
synthetic groups pass. Library/Apple jobs skip; artifacts0, XML0, native0,
signing/install/launch/query/profile/leaks0. Exact994/1071 Git freeze independently
verified in `independent-review/`; fixed error domains/codes and frame-ownership
parser have no new Apple outcome.

The actual failure is `test_desktop_saver_state_focus.py:149`, not an Apple launch
or signing error. [Owning repair](../serial-profile-guard-recovery-20261031/README.md)
preserves workflow serial1/default2 and changes only the stale guard. Request and
public metadata are archived; original tooling log remains private. #141 stays
open, previous strict/timeout/pre-PID failures remain failed/unfixed/unwaived,
actual native launch cause unknown. One finite failed-profile workload only next;
accepted UIImage/stress suites and unverified releases are not requested.
