#!/usr/bin/env bash
# Legacy output bypasses the required native manifest validation.
set -euo pipefail
cat >&2 <<'MESSAGE'
This legacy cross-build helper is disabled because it produces unverified resources.
From the repository root, use the resource-aware runner to execute
:calf-file-picker:prepareNativeResources for the actual host.
See docs/testing/README.md for verified prebuilt bundles and release requirements.
MESSAGE
exit 2
