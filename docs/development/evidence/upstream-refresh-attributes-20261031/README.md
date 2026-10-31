# Preserve upstream discussion bytes without widening whitespace exceptions

The October31 refresh staged original author CRLF/trailing spaces. Only the
quoted-author `docs/development/upstream-refresh-*/drafts/**` archive subtree now
uses `-text -whitespace`, matching the existing byte-preserving upstream archive
policy. Current source and refresh README whitespace checks remain enabled.

[Two real-Git regression methods](review.json) retain one initial failure and
then both pass. They check original bytes survive archive checkout while current
source/README bad whitespace still fails. Archived original text was not trimmed.
These are Git/tooling checks, **zero library/native executions or issue closures**.
The source/test/attribute change is already in61003963; these receipts are additive.
