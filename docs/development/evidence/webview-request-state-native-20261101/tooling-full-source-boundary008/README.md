# Full-source manual-reset refusal before legacy projection

Actual iOS41270913975 and camera41270929101 at7cb5f46d FAILED in one shared
tooling method;1747CI methods/1746pass each, ZERO native/artifacts. Exact original
line377 appends a manual errorsForCurrentRequest reset after new Stop helpers.
compiled_request_source intentionally projects to the byte-frozen old fixture,
so checking forbidden resets only afterward discarded that appended mutation.

Only the owning source guard now refuses manual request resets on full input
before projection. Native sources, public Stop, exact old/new fixture assertions,
HTTP bounds, original filters and cleanup are unchanged. A new method covers
legacy tail, separate helper tail and the separate native method. Original
source guard remains red in its original run. Local red executes two methods/
three failure events (two are subtests), then the two failed methods pass2/2
without replaying accepted unrelated methods. Initial harness count refusal is
retained; no red rerun or native/platform success is inferred.

Recover only the same stopped iOS request2+DNS1 and camera Dont-keep1 at a new
reviewed source revision. #13/#64 remain open. No publishing/consumer/ABI/
security/readiness clearance. Original reports/log bodies stay private hashed.
