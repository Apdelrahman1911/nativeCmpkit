"""Bounded observations of an already verified PRIVATE failed PREPARE capture.

Pure data only: no reads, subprocesses, exceptions/messages/paths exported, or
native acceptance. Every exported string is a fixed enum or trusted source ID.
Even a classified compiler/task line does NOT establish the underlying cause.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

MAX_PRIVATE_BYTES = 64 * 1024
MAX_PUBLIC_BYTES = 4096
MAX_LINES = 4096
MAX_LINE_BYTES = 4096
MAX_POSITION = 1000000
SOURCES = {
    "awt_generation_test": "calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeMacOsParentLeaseGenerationTest.kt",
    "native_convention": "convention-plugins/src/main/kotlin/NativeLibraries.kt",
    "picker_module_build": "calf-file-picker/build.gradle.kts",
    "root_build": "build.gradle.kts",
    "root_settings": "settings.gradle.kts",
}
TASKS = {
    "desktop_production_compiler": ":calf-file-picker:compileKotlinDesktop",
    "desktop_resources": ":calf-file-picker:desktopProcessResources",
    "desktop_test_compiler": ":calf-file-picker:compileTestKotlinDesktop",
    "host_native_build": ":calf-file-picker:buildNativeLib",
    "native_resources": ":calf-file-picker:verifyNativeResources",
    "runtime_classpath": ":calf-file-picker:writeNativeTestRuntimeClasspath",
}
REQUIRED_TASK_IDS = ("desktop_resources", "runtime_classpath", "native_resources")
NATIVE_TASK_IDS = (*REQUIRED_TASK_IDS, "host_native_build")
# Tier0 is a concrete runtime/transport exception family, tier1 a compiler/
# plugin stage family, tier2 a broad execution wrapper. This selects an observed
# enum, NOT a root cause. Classes/messages/paths are never exported.
TRACE_CLASSES = {
    "java.lang.NoSuchMethodError": (0, "gradle_api_linkage_observed", "gradle_wrapper_api_linkage_observed"),
    "java.lang.NoSuchFieldError": (0, "gradle_api_linkage_observed", "gradle_wrapper_api_linkage_observed"),
    "java.lang.AbstractMethodError": (0, "gradle_api_linkage_observed", "gradle_wrapper_api_linkage_observed"),
    "java.lang.NoClassDefFoundError": (0, "gradle_class_loading_observed", "gradle_wrapper_class_loading_observed"),
    "java.lang.ClassNotFoundException": (0, "gradle_class_loading_observed", "gradle_wrapper_class_loading_observed"),
    "java.lang.UnsupportedClassVersionError": (0, "gradle_bytecode_runtime_observed", "gradle_wrapper_bytecode_runtime_observed"),
    "java.lang.OutOfMemoryError": (0, "gradle_jvm_memory_observed", "gradle_wrapper_jvm_memory_observed"),
    "javax.net.ssl.SSLHandshakeException": (0, "gradle_tls_observed", "gradle_wrapper_tls_observed"),
    "sun.security.provider.certpath.SunCertPathBuilderException": (0, "gradle_tls_observed", "gradle_wrapper_tls_observed"),
    "java.net.UnknownHostException": (0, "gradle_dns_observed", "gradle_wrapper_dns_observed"),
    "java.net.SocketTimeoutException": (0, "gradle_timeout_observed", "gradle_wrapper_timeout_observed"),
    "java.io.FileNotFoundException": (0, "gradle_missing_file_observed", "gradle_wrapper_download_missing_observed"),
    "org.gradle.kotlin.dsl.support.ScriptCompilationException": (1, "gradle_script_compilation_observed", None),
    "org.jetbrains.kotlin.gradle.tasks.CompilationErrorException": (1, "gradle_kotlin_compiler_observed", None),
    "org.gradle.api.plugins.UnknownPluginException": (1, "gradle_plugin_resolution_observed", None),
    "org.gradle.api.UnknownTaskException": (1, "gradle_task_lookup_observed", None),
    "org.gradle.internal.resolve.ModuleVersionNotFoundException": (2, "gradle_dependency_resolution_observed", None),
    "org.gradle.internal.resolve.ModuleVersionResolveException": (2, "gradle_dependency_resolution_observed", None),
    "org.gradle.process.internal.ExecException": (2, "gradle_subprocess_observed", None),
    "java.io.IOException": (2, "gradle_io_observed", "gradle_wrapper_download_io_observed"),
    # Fixed input-only family names; none is evidence about the original
    # unavailable capture. Project configuration is a broad stage wrapper
    # below all preexisting tiers, never a diagnosis of SDK/configuration.
    "com.android.builder.errors.EvalIssueException": (1, "gradle_android_configuration_observed", None),
    "org.gradle.api.internal.artifacts.verification.exceptions.DependencyVerificationException": (1, "gradle_dependency_verification_observed", None),
    "org.gradle.launcher.daemon.client.DaemonDisappearedException": (1, "gradle_daemon_disappearance_observed", None),
    "org.gradle.api.ProjectConfigurationException": (3, "gradle_project_configuration_observed", None),
}
TRACE_CODES = frozenset(code for row in TRACE_CLASSES.values() for code in row[1:] if code is not None)
CONTEXT_CODES = frozenset(("gradle_failure_frame_absent_observed", "gradle_failure_frame_partial_observed",
                           "gradle_failure_frame_multiple_observed", "gradle_failure_frame_order_refused_observed",
                           "gradle_wrapper_context_refused_observed", "gradle_task_banners_without_trace_observed",
                           "gradle_build_trace_without_allowed_family_observed", "gradle_wrapper_trace_without_allowed_family_observed"))

UNAVAILABLE_CODES = frozenset(("none", "ineligible_phase", "capture_unavailable", "capture_identity_refused",
                               "UTF8_refused", "diagnostic_limit", "remaining_budget_refused", "classifier_error"))
PUBLIC_CHOICES = {
    "status": {"classified", "unclassified", "unavailable"},
    "category": {"kotlin_compilation", "java_compilation", "rust_compilation", "gradle_configuration",
                 "dependency_resolution", "native_resource_task", "task_execution", "unknown"},
    "diagnostic_code": {"kotlin_unresolved_reference", "kotlin_type_mismatch", "kotlin_overload_ambiguity", "kotlin_type_inference",
                        "java_compiler_error", "rust_compiler_error", "gradle_plugin_resolution", "gradle_configuration_error",
                        "dependency_resolution_error", "required_native_task_failed", "unknown"} | TRACE_CODES | CONTEXT_CODES,
    "unavailable_code": UNAVAILABLE_CODES,
}


def unavailable(code: str) -> dict:
    # A caller cannot accidentally turn an exception message into public text.
    if code not in UNAVAILABLE_CODES or code == "none":
        code = "classifier_error"
    return {"schema_version": 1, "status": "unavailable", "category": "unknown", "diagnostic_code": "unknown",
            "failed_task_id": None, "location": None, "ambiguity": False, "cause_established": False,
            "required_task_states": {key: "unobserved" for key in REQUIRED_TASK_IDS}, "unavailable_code": code}


def _number(text: str) -> int | None:
    if not re.fullmatch(r"[1-9][0-9]{0,6}", text):
        return None
    value = int(text)
    return value if value <= MAX_POSITION else None


def bounded_public(value: dict) -> dict:
    """Final fixed-schema guard, including a classifier's secondary malfunction."""
    if type(value) is not dict or set(value) != set(unavailable("classifier_error")):
        return unavailable("classifier_error")
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1 or
            value["cause_established"] is not False or type(value["ambiguity"]) is not bool or
            any(type(value[key]) is not str or value[key] not in choices for key, choices in PUBLIC_CHOICES.items()) or
            value["failed_task_id"] is not None and value["failed_task_id"] not in TASKS):
        return unavailable("classifier_error")
    states, location = value["required_task_states"], value["location"]
    if (type(states) is not dict or set(states) != set(REQUIRED_TASK_IDS) or
            any(type(state) is not str or state not in {"unobserved", "executed_line", "cached_line", "failed_line", "ambiguous"}
                for state in states.values())):
        return unavailable("classifier_error")
    if location is not None:
        if (type(location) is not dict or set(location) != {"source_id", "line", "column"} or
                location["source_id"] not in SOURCES or type(location["line"]) is not int or
                not 1 <= location["line"] <= MAX_POSITION or
                location["column"] is not None and (type(location["column"]) is not int or not 1 <= location["column"] <= MAX_POSITION)):
            return unavailable("classifier_error")
    if len(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")) > MAX_PUBLIC_BYTES:
        return unavailable("diagnostic_limit")
    return value


def _locations(root: Path) -> dict[str, str]:
    # root comes from the controller's already qualified checkout, never log text.
    # These are lexical guards, NOT a substitute for its filesystem custody.
    name = root.as_posix()
    if (not root.is_absolute() or name == "/" or len(name) > 4096 or
            any(ord(char) < 32 for char in name) or "\\" in name or ":" in name or
            any(part in {".", ".."} for part in root.parts)):
        return {}
    return {literal: key for key, relative in SOURCES.items()
            for literal in ((root / relative).as_posix(), (root / relative).as_uri())}


def _compiler(line: str, locations: dict[str, str]) -> tuple | None:
    for literal, key in locations.items():
        # The entire path/URI must equal the trusted root plus a fixed file.
        prefix = re.escape("e: " + literal)
        match = (re.fullmatch(prefix + r":([0-9]+):([0-9]+) (?P<message>[^\r\n]+)", line) or
                 re.fullmatch(prefix + r": \(([0-9]+), ([0-9]+)\): (?P<message>[^\r\n]+)", line))
        if match is None:
            continue
        row, column = _number(match[1]), _number(match[2])
        if row is None or column is None:
            return None
        message = match["message"]
        phrases = ((r"Unresolved reference(?:[ :.'\"].*)?", "kotlin_unresolved_reference"),
                   (r"(?:Argument type mismatch|Type mismatch)(?:[ :.].*)?", "kotlin_type_mismatch"),
                   (r"Overload resolution ambiguity(?:[ :.].*)?", "kotlin_overload_ambiguity"),
                   (r"(?:Cannot infer type for this parameter|Not enough information to infer type)(?:[ :.].*)?", "kotlin_type_inference"))
        for grammar, code in phrases:
            if re.fullmatch(grammar, message):
                return ("kotlin_compilation", code, {"source_id": key, "line": row, "column": column})
    return None


def _gradle_trace_observation(lines: list[str]) -> tuple[str, bool]:
    """One fixed exception-family observation; never resolve old ambiguity."""
    failure, what, trace = ("FAILURE: Build failed with an exception.", "* What went wrong:", "* Exception is:")
    footer = [index for index, line in enumerate(lines) if re.fullmatch(r"BUILD FAILED in [^\r\n]+", line)]
    build = (lines.count(failure) == lines.count(what) == lines.count(trace) == len(footer) == 1 and
             lines.index(failure) < lines.index(what) < lines.index(trace) < footer[0])
    main_grammar = r'Exception in thread "main" ([A-Za-z_$][A-Za-z0-9_.$]{0,255})(?::[^\r\n]*)?'
    mains = [index for index, line in enumerate(lines) if re.fullmatch(main_grammar, line.strip())]
    wrapper_frames = [index for index, line in enumerate(lines) if re.fullmatch(
        r"at org\.gradle\.wrapper\.(?:Download|Install)\.[A-Za-z_$][A-Za-z0-9_$]{0,127}"
        r"\((?:[A-Za-z0-9_.-]{1,128}:[0-9]{1,7}|Unknown Source|Native Method)\)", line.strip())]
    # Bootstrap is a distinct context, not merely an incomplete Gradle build.
    # A fixed wrapper frame must belong to the selected AFTER-main trace, and
    # official/partial Gradle frame or task markers must be entirely absent.
    build_markers = any(line.strip().startswith(("FAILURE:", "* What went wrong:", "* Exception is:", "BUILD FAILED"))
                        for line in lines)
    task_markers = any(line.strip().startswith("> Task ") for line in lines)
    wrapper = (not build_markers and not task_markers and len(mains) == 1 and
               any(index > mains[0] for index in wrapper_frames))
    if not build and not wrapper:
        # Presence/layout observations only. Never promote a rejected
        # partial/mixed frame into an exception-family or primary result.
        counts = (lines.count(failure), lines.count(what), lines.count(trace), len(footer))
        if any(count > 1 for count in counts):
            code = "gradle_failure_frame_multiple_observed"
        elif counts == (1, 1, 1, 1):
            code = "gradle_failure_frame_order_refused_observed"
        elif build_markers:
            code = "gradle_failure_frame_partial_observed"
        elif mains or wrapper_frames:
            code = "gradle_wrapper_context_refused_observed"
        elif task_markers:
            code = "gradle_task_banners_without_trace_observed"
        else:
            code = "gradle_failure_frame_absent_observed"
        return code, bool(wrapper_frames and len(mains) > 1)
    selected = lines[lines.index(trace) + 1:footer[0]] if build else lines[mains[0]:]
    codes = {0: set(), 1: set(), 2: set(), 3: set()}
    for raw in selected:
        line = raw.strip()
        if not line.startswith(("Caused by: ", 'Exception in thread "main" ', "java.", "javax.", "sun.", "org.gradle.", "org.jetbrains.kotlin.", "com.android.builder.errors.")):
            continue
        match = re.fullmatch(r"(?:Caused by: )?([A-Za-z_$][A-Za-z0-9_.$]{0,255})(?::[^\r\n]*)?", line)
        if match is None and wrapper:
            match = re.fullmatch(main_grammar, line)
        observed = TRACE_CLASSES.get(match[1]) if match else None
        if observed is not None:
            tier, code, wrapper_code = observed
            codes[tier].add(wrapper_code if wrapper and wrapper_code is not None else code)
    for tier in (0, 1, 2, 3):
        if codes[tier]:
            return (next(iter(codes[tier])), False) if len(codes[tier]) == 1 else ("unknown", True)
    return ("gradle_build_trace_without_allowed_family_observed" if build else
            "gradle_wrapper_trace_without_allowed_family_observed"), False


def classify(root: Path, body: str) -> dict:
    """Report fixed observations, never source text or an inferred root cause."""
    if not isinstance(root, Path) or type(body) is not str:
        return unavailable("classifier_error")
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeError:
        return unavailable("UTF8_refused")
    if len(encoded) > MAX_PRIVATE_BYTES:
        return unavailable("diagnostic_limit")
    lines = body.splitlines()
    if (len(lines) > MAX_LINES or any(len(line.encode("utf-8")) > MAX_LINE_BYTES for line in lines) or
            any(ord(char) < 32 and char not in "\t\r\n" for char in body)):
        return unavailable("diagnostic_limit")
    locations = _locations(root)
    if not locations:
        return unavailable("classifier_error")
    result = unavailable("classifier_error")
    result.update(status="unclassified", unavailable_code="none")
    candidates, selected_locations, failed_tasks = [], [], []
    observed = {key: [] for key in REQUIRED_TASK_IDS}
    ambiguous = False
    unsupported = False
    task_ids = {task: key for key, task in TASKS.items()}
    for line in lines:
        task = re.fullmatch(r"> Task (:[A-Za-z0-9_:.\-]+)(?: (UP-TO-DATE|FROM-CACHE|FAILED|NO-SOURCE|SKIPPED))?", line)
        if task:
            key = task_ids.get(task[1])
            if key in observed:
                state = {None: "executed_line", "UP-TO-DATE": "cached_line", "FROM-CACHE": "cached_line",
                         "FAILED": "failed_line"}.get(task[2], "ambiguous")
                observed[key].append(state)
            if task[2] == "FAILED":
                if key is None:
                    unsupported = True
                else:
                    failed_tasks.append(key)
            continue
        failure = re.fullmatch(r"Execution failed for task '(:[A-Za-z0-9_:.\-]+)'\.", line)
        if failure:
            key = task_ids.get(failure[1])
            if key is None:
                unsupported = True
            else:
                failed_tasks.append(key)
            continue
        compiled = _compiler(line, locations) if line.startswith("e: ") else None
        if compiled:
            candidates.append(compiled[:2])
            selected_locations.append(compiled[2])
            continue
        if line.startswith("e: "):
            unsupported = True
            continue
        where = re.fullmatch(r"(Build|Settings) file '([^'\r\n]+)' line: ([0-9]+)", line)
        if where:
            key, row = locations.get(where[2]), _number(where[3])
            if key in {"picker_module_build", "root_build", "root_settings"} and row is not None:
                selected_locations.append({"source_id": key, "line": row, "column": None})
            else:
                unsupported = True
            continue
        if re.fullmatch(r"error: (?:invalid source release: [0-9]{1,7}|release version [0-9]{1,7} not supported)", line):
            candidates.append(("java_compilation", "java_compiler_error"))
        elif re.fullmatch(r"error\[E[0-9]{4}\]: [^\r\n]+", line):
            candidates.append(("rust_compilation", "rust_compiler_error"))
        elif re.fullmatch(r"Plugin \[id: '[A-Za-z0-9_.-]{1,128}'(?:, version: '[A-Za-z0-9_.+:-]{1,128}')?\] was not found in any of the following sources:", line):
            candidates.append(("gradle_configuration", "gradle_plugin_resolution"))
        elif line == "Script compilation errors:":
            candidates.append(("gradle_configuration", "gradle_configuration_error"))
        elif re.fullmatch(r"(?:> )?Could not resolve all (?:files|dependencies|artifacts) for configuration '[^'\r\n]{1,256}'\.", line):
            candidates.append(("dependency_resolution", "dependency_resolution_error"))
        elif line.startswith(("error:", "error[", "Execution failed for task", "Build file ", "Settings file ")):
            unsupported = True
    for key, states in observed.items():
        if states:
            result["required_task_states"][key] = states[0] if len(states) == 1 else "ambiguous"
            if len(states) != 1 or states[0] == "ambiguous":
                ambiguous = True
    unique_failed = set(failed_tasks)
    if len(unique_failed) > 1 or len(candidates) > 1 or len(selected_locations) > 1:
        ambiguous = True
    if ambiguous or unsupported:
        result["ambiguity"] = ambiguous
    else:
        key = next(iter(unique_failed)) if unique_failed else None
        result["failed_task_id"] = key
        if selected_locations:
            result["location"] = selected_locations[0]
        if candidates:
            result.update(status="classified", category=candidates[0][0], diagnostic_code=candidates[0][1])
        elif key is not None:
            result.update(status="classified", category="native_resource_task" if key in NATIVE_TASK_IDS else "task_execution",
                          diagnostic_code="required_native_task_failed" if key in NATIVE_TASK_IDS else "unknown")
    if result["status"] == "unclassified":
        # Fallback is explicitly an OBSERVATION. Original status/category/task/
        # source selection and ambiguity refusals remain, with cause=false.
        code, trace_ambiguity = _gradle_trace_observation(lines)
        result["diagnostic_code"] = code
        result["ambiguity"] = result["ambiguity"] or trace_ambiguity
    return bounded_public(result)
