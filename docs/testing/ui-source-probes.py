#!/usr/bin/env python3
"""Run small, cache-only Kotlin probes against the immutable UI audit baseline.

NOT a Gradle, Compose, UIKit or platform integration build. Reads source using
`git show`, compiles exact common algorithm/model sources, removes only @Test
registration from existing tests and invokes their unchanged assertion bodies.
Stubs: Compose Immutable; Material opt-in marker/SelectableDates/AllDates;
AdaptiveDatePickerState fields used by common helper extensions; Modifier and
semantics action capture for one extracted helper; UIDevice version string.

Extracted bodies: iOS time constructor init guard, native dropdown availability
predicate, Cupertino slider semantic helper. Defect assertions deliberately pass
when the baseline bug is observed. No native graphics or pointer event is run.
No downloads/cache mutation; temporary source/JAR output is removed on exit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
ROOT = Path(__file__).resolve().parents[2]
UI = "calf-ui/src/{}/kotlin/com/mohamedrejeb/calf/ui/{}"
COMMON = [
    "datepicker/DateBounds.kt", "datepicker/SelectableDays.kt",
    "datepicker/DateRangeSelection.kt", "dialog/AdaptiveAlertDialogActions.kt",
    "dialog/uikit/AlertDialogIosAction.kt", "dialog/uikit/AlertDialogIosActionStyle.kt",
]
TESTS = [
    "datepicker/TestDates.kt", "datepicker/DateBoundsSelectableDatesTest.kt",
    "datepicker/DateBoundsTest.kt", "datepicker/DateRangeSelectionTest.kt",
    "dialog/AdaptiveAlertDialogActionsTest.kt",
]
STUBS = {
    "ComposeTypes.kt": """package androidx.compose.runtime
annotation class Immutable
""",
    "MaterialTypes.kt": """package androidx.compose.material3
@RequiresOptIn annotation class ExperimentalMaterial3Api
interface SelectableDates {
    fun isSelectableDate(utcTimeMillis: Long): Boolean = true
    fun isSelectableYear(year: Int): Boolean = true
}
object DatePickerDefaults { val AllDates: SelectableDates = object : SelectableDates {} }
""",
    "DateState.kt": """package com.mohamedrejeb.calf.ui.datepicker
import androidx.compose.material3.SelectableDates
class AdaptiveDatePickerState(var selectedDateMillis: Long?, var selectableDates: SelectableDates)
""",
}


def read(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, text=True)


def extract_block(source, marker):
    """Balanced braces, for the three fixed audited bodies (no braces in strings)."""
    start = source.index(marker)
    brace = source.index("{", start)
    depth = 1
    cursor = brace + 1
    while depth:
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    return source[start:cursor]


def cached_jar(cache, group, artifact, version):
    candidates = sorted((cache / group / artifact / version).glob(f"*/{artifact}-{version}.jar"))
    if len(candidates) != 1:
        raise SystemExit(f"Need one cached {group}:{artifact}:{version}; no downloads attempted")
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path.home()/".gradle/caches/modules-2/files-2.1")
    args = parser.parse_args()
    versions = [
        ("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-build-tools-api", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-script-runtime", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-stdlib", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-reflect", "1.6.10"),
        ("org.jetbrains.kotlin", "kotlin-daemon-embeddable", "2.4.20"),
        ("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.8.0"),
        ("org.jetbrains", "annotations", "13.0"),
        ("org.jetbrains.kotlin", "kotlin-test", "2.4.20"),
    ]
    jars = {artifact: cached_jar(args.cache, group, artifact, version)
            for group, artifact, version in versions}
    print(f"UI source probes baseline={BASELINE}", flush=True)
    print("Compiler2.4.20, stdlib2.4.20, kotlin-test2.4.20; compiler bootstrap reflect1.6.10/coroutines1.8.0.", flush=True)
    print("No app coroutine code, Compose runtime, Material implementation or UIKit is loaded.", flush=True)
    print("Heap limit256MiB; all sources/JAR output isolated in TemporaryDirectory; cache read-only.", flush=True)
    subprocess.run(["java", "-version"], check=True)
    with tempfile.TemporaryDirectory(prefix="nativecmpkit-ui-probes-") as tmp:
        work = Path(tmp)
        files = []
        manifest = []
        def write(name, text):
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            files.append(str(path))
        calls = []
        for ss, names in [("commonMain", COMMON), ("commonTest", TESTS)]:
            for name in names:
                path = UI.format(ss, name)
                text = read(path)
                manifest.append({"path": path, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                 "transform": "remove @Test annotation/import only" if ss=="commonTest" else "unchanged"})
                if ss == "commonTest":
                    package = re.search(r"^package (.+)$", text, re.M).group(1)
                    cls = re.search(r"^class (\w+)", text, re.M)
                    if cls:
                        methods = re.findall(r"@Test\s+fun (`[^`]+`|\w+)\(", text)
                        for method in methods:
                            label = (cls.group(1)+"."+method.strip("`")).replace('"', '\\"')
                            calls.append(f'    checkCase("{label}") {{ {package}.{cls.group(1)}().{method}() }}')
                    text = re.sub(r"^import kotlin.test.Test\s*\n", "", text, flags=re.M)
                    text = re.sub(r"^\s*@Test\s*\n", "\n", text, flags=re.M)
                write(ss+"/"+name, text)
        for name, body in STUBS.items():
            write("stubs/"+name, body)

        time_path = UI.format("iosMain", "timepicker/AdaptiveTimePickerState.ios.kt")
        time_body = extract_block(read(time_path), "    init {")
        write("TimeGuard.kt", "class ExtractedTimeGuard(initialHour: Int, initialMinute: Int) {\n"+time_body+"\n}\n")
        drop_path = UI.format("iosMain", "dropdown/AdaptiveDropDown.ios.kt")
        drop_body = extract_block(read(drop_path), "private fun isPerformPrimaryActionAvailable()")
        write("Dropdown.kt", """object UIDevice {
    val currentDevice = this
    var systemVersion: String = "17.4"
}
"""+drop_body+"\nfun dropdownAvailable(version: String): Boolean { UIDevice.systemVersion=version; return isPerformPrimaryActionAvailable() }\n")
        slider_path = UI.format("iosMain", "slider/CupertinoSlider.kt")
        slider_body = extract_block(read(slider_path), "private fun Modifier.cupertinoSliderSemantics(")
        write("SliderSemantics.kt", """import kotlin.math.abs
class Modifier { var action: ((Float) -> Boolean)? = null }
class SemanticsReceiver(private val modifier: Modifier) {
    fun disabled() {}
    fun setProgress(action: (Float) -> Boolean) { modifier.action = action }
}
fun Modifier.semantics(block: SemanticsReceiver.() -> Unit): Modifier {
    SemanticsReceiver(this).block(); return this
}
fun Modifier.progressSemantics(value: Float, range: ClosedFloatingPointRange<Float>, steps: Int) = this
fun lerp(start: Float, stop: Float, fraction: Float): Float = start + (stop-start)*fraction
"""+slider_body+"""
fun requestSliderProgress(target: Float): Float {
    var output=Float.NaN
    val modifier=Modifier().cupertinoSliderSemantics(
        value=0f, enabled=true, onValueChange={output=it}, valueRange=-1f..1f, steps=3
    )
    check(modifier.action!!.invoke(target))
    return output
}
""")
        for path, body in [(time_path,time_body), (drop_path,drop_body), (slider_path,slider_body)]:
            manifest.append({"path":path,"sha256":hashlib.sha256(read(path).encode()).hexdigest(),
                             "transform":"extract exact audited body; surrounding platform types stubbed",
                             "extracted_sha256":hashlib.sha256(body.encode()).hexdigest()})
        assert len(calls)==32, "Unexpected baseline test inventory"
        write("Harness.kt", """private var total=0
private fun checkCase(name: String, block: () -> Unit) {
    block(); total++; println("PASS $name")
}
fun main() {
"""+"\n".join(calls)+"""
    println("EXISTING COMMON ASSERTION BODIES: $total/32 passed (algorithm/type stubs only)")
    checkCase("UI-009 exact guard accepts invalid minute -1 and60") {
        ExtractedTimeGuard(12,-1); ExtractedTimeGuard(12,60)
        check(runCatching { ExtractedTimeGuard(24,30) }.isFailure)
        println("  hour24 rejected; minute-1 and60 accepted")
    }
    checkCase("UI-024 exact native availability comparator") {
        val results=listOf("17.3","17.4","17.10","18.0","26.0","26.4").associateWith(::dropdownAvailable)
        check(results==linkedMapOf("17.3" to false,"17.4" to true,"17.10" to true,"18.0" to false,"26.0" to false,"26.4" to true))
        println("  $results;18.0/26.0 wrongly rejected")
    }
    checkCase("UI-033 exact semantic helper fails negative discrete snapping") {
        val actual=requestSliderProgress(-0.7f)
        check(actual == -0.7f && actual != -0.5f)
        check(requestSliderProgress(0.7f) == 0.5f)
        println("  target-0.7 -> $actual (expected-0.5); positive0.7 control ->0.5")
    }
    println("SUMMARY $total/35 checks passed:32 existing algorithm tests +3 expected defect characterizations; no defects fixed")
}
""")
        print("SOURCE MANIFEST (source digests and transformations):", flush=True)
        print(json.dumps(manifest, indent=2), flush=True)
        cp = os.pathsep.join(str(jars[n]) for n in ["kotlin-stdlib","kotlin-test","annotations"])
        jar = str(work/"ui-probes.jar")
        print("COMMAND java -Xmx256m -cp <cached compiler jars> org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath <stdlib2.4.20:kotlin-test2.4.20:annotations13.0> -d <temporary>/ui-probes.jar <copied sources/stubs/harness>", flush=True)
        subprocess.run(["java","-Xmx256m","-cp",os.pathsep.join(map(str,jars.values())),
                        "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler","-no-stdlib","-no-reflect",
                        "-classpath",cp,"-d",jar,*files],check=True,timeout=120)
        print("COMMAND java -Xmx256m -cp <temporary JAR:stdlib:kotlin-test:annotations> HarnessKt", flush=True)
        subprocess.run(["java","-Xmx256m","-cp",jar+os.pathsep+cp,"HarnessKt"],check=True,timeout=30)


if __name__ == "__main__":
    main()
