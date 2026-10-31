# Bounded Apple launch-error observations

The existing failed-profile query now retains up to sixteen fixed NSError
domain/signed-32-bit-code pairs from exact owned bundle/time/system-process rows.
It does not retain reasons, paths, addresses or arbitrary domains, interpret a
causal chain, retry launch, change signing or relax native/profile assertions.

[Integration review](review.json): ten new and six related modeled methods pass
(0.113s/0.031s), with the original missing-field red retained. Private ten-method
results overlap; they are not twenty distinct checks. The exact applied patch
reconstructs990/1067 integrated inputs from the recorded baseline; those maps
match the after-test maps. This is not an Apple execution or a release gate.

Actual41044446342 remains failed before reported PID/activation; its launch cause
is unknown. The native host/profile preparation matched accepted d2888301 source
bytes, not a new executed binary. [Public references](proposal/public-reference-observations.json)
explain domain-specific NSError codes without decoding private launch codes.

An independent review also found filename-only allocation-frame attribution in
the existing profile reader. That separate correction is required before the
next finite request. **Zero new Apple/native/profile executions; #141 stays open.**
Prior strict startup/record/timeout failures, same-PID zero-leak/owned allocation
requirements, dependency/security/readiness and publishing gates remain.

[Manifest](manifest.json) binds selected public/modeled evidence; no actual raw
system log, trace, private binary or credential is archived here.
