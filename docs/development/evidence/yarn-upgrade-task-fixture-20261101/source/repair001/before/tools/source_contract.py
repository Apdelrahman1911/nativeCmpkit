#!/usr/bin/env python3
"""New private source-only completeness checks; NEVER Kotlin typing or actual KGP proof."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HELPER_SHA256 = "6473a953ad6c95e0eb00f0e79e2275aac0731976db06356b73bcfa6abfac0f14"


def checks(helper: bytes, root: str, settings: str, child: str) -> list[dict]:
    rows = []
    def check(name, value):
        rows.append({"name": name, "passed": bool(value), "scope": "source-only-not-Kotlin-or-runtime"})
    check("unchanged-reviewed-62-line-helper", hashlib.sha256(helper).hexdigest() == HELPER_SHA256 and len(helper.splitlines()) == 62)
    text = helper.decode("utf-8")
    check("actual-upgrade-class-observer", "withType(YarnLockUpgradeTask::class.java)" in text and "upgrade.dependsOn(gate)" in text)
    check("root-ordering-without-self-edge", "if (task !is RefuseOrdinaryYarnUpgradeTask) task.mustRunAfter(gate)" in text)
    check("fresh-TaskAction-exact-denial", "@TaskAction" in text and 'throw GradleException("NCYUG-actual-upgrade-forbidden-before-root-task-actions")' in text)
    check("explicit-unsupported-invocation-modes", all(x in text for x in ("isConfigurationCacheRequested", "excludedTaskNames", "isConfigureOnDemand", "bootstrap-and-unknown-modes-held")))
    check("typed-actual-upgrade-providers", all(x in root for x in ('tasks.named("kotlinUpgradeYarnLock", YarnLockUpgradeTask::class.java)', 'tasks.named("kotlinWasmUpgradeYarnLock", YarnLockUpgradeTask::class.java)')))
    check("typed-actual-primary-providers", all(x in root for x in ('tasks.named("kotlinNpmInstall", KotlinNpmInstallTask::class.java)', 'tasks.named("kotlinWasmNpmInstall", KotlinNpmInstallTask::class.java)')))
    check("indirect-actual-provider-edges", "dependsOn(jsUpgradeProvider)" in root and "dependsOn(wasmUpgradeProvider)" in root)
    check("actual-object-graph-and-ordering", "graph.hasTask(gate)" in root and "mustRunAfter.getDependencies" in root and "taskDependencies.getDependencies" in root)
    check("fresh-graph-and-result-receipts", all(x in root for x in ('writeFresh("graph.json"', 'writeFresh("result.json"', "StandardOpenOption.CREATE_NEW", "gradle.buildFinished", "task.state.executed", "task.state.failure")))
    check("bounded-fresh-action-journal", 'writeFresh("action-%04d.json"' in root and "NCYB-FIXTURE-ACTION path={}" in root and "observedActions.size < 128" in root)
    check("tripwire-failure-is-not-denial", "NCYB-unexpected-root-task-action" in root and "allowed_by_fixture_tripwire" in root and "exact_denial_in_failure_chain" in root)
    check("sentinel-action-has-own-receipt", 'writeFresh("sentinel.json"' in root and "NCYB-FIXTURE-SENTINEL-RAN" in root)
    check("only-four-owning-cases", 'setOf("U1", "U2", "U3", "U4")' in root and "gradle.startParameter.taskNames == expectedRequests" in root)
    check("no-binding-alternative-or-fake-upgrade", not any(x in root for x in ("OrdinaryYarnTaskBindingProbe", "unknown-primary", "unknown-lock", "tooling-warm", 'tasks.register("kotlinUpgradeYarnLock"', 'tasks.register("kotlinWasmUpgradeYarnLock"')))
    check("relative-frozen-settings-no-placeholder", '@FROZEN_REPO_ROOT@' not in settings and 'includeBuild("../convention-plugins")' in settings and 'from(files("../gradle/libs.versions.toml"))' in settings)
    check("late-child-real-js-and-wasm-targets", 'alias(libs.plugins.kotlinMultiplatform)' in child and 'js { browser() }' in child and 'wasmJs { browser() }' in child)
    check("pinned-version-and-store-policy-retained", all(x in root for x in ('"24.16.0"', '"1.22.22"', 'yarnLockMismatchReport.set(YarnLockMismatchReport.FAIL)', 'yarnLockAutoReplace.set(false)', 'ignoreScripts.set(true)', 'reportNewYarnLock.set(true)')))
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--helper", type=Path, required=True)
    p.add_argument("--root-build", type=Path, required=True)
    p.add_argument("--settings", type=Path, required=True)
    p.add_argument("--child", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rows = checks(args.helper.read_bytes(), args.root_build.read_text(), args.settings.read_text(), args.child.read_text())
    receipt = {"schema": 1, "scope": "new-private-source-contract-only", "checks": len(rows), "passed": sum(x["passed"] for x in rows), "actual_gradle_kotlin_node_yarn_native_executions": 0, "checks_detail": rows}
    with args.output.open("x") as f: json.dump(receipt, f, indent=2, sort_keys=True); f.write("\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "checks_detail"}, sort_keys=True))
    return int(any(not x["passed"] for x in rows))


if __name__ == "__main__":
    raise SystemExit(main())
