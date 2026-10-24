#!/usr/bin/env python3
"""Print sanitized per-task JUnit XML counts; never infer execution from no reports.

Only individual build/test-results task reports are counted. An allTests aggregate
is excluded to avoid counting platform tests twice. Standard output/error and
failure text are intentionally not copied: they may contain application data.
Reports may come from a cache, so inspect Gradle task outcomes as well.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


class NoDtdTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, public_id, system_id):
        raise ValueError("DTD/entity declarations are outside JUnit report scope")


def summarize(root):
    reports = []
    errors = []
    by_task = defaultdict(lambda: dict(tests=0, failures=0, errors=0, skipped=0))
    for path in sorted(root.glob("**/build/test-results/**/TEST-*.xml")):
        relative = path.relative_to(root)
        if "allTests" in relative.parts:
            continue
        try:
            payload = path.read_bytes()
            # Gradle JUnit reports need no DTD/entities. Reject via the XML parser
            # callback, which also handles non-UTF8 document encodings correctly.
            document = ET.fromstring(payload, parser=ET.XMLParser(target=NoDtdTreeBuilder()))
            suites = [document] if document.tag == "testsuite" else document.findall("testsuite")
            if document.tag not in ("testsuite", "testsuites") or not suites:
                raise ValueError("unrecognized JUnit document")
            counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
                      for key in ("tests", "failures", "errors", "skipped")}
            task = relative.parts[relative.parts.index("test-results") + 1]
            module = "/".join(relative.parts[:relative.parts.index("build")]) or ":"
            reports.append(dict(path=str(relative), module=module, task=task, **counts))
            for key, value in counts.items():
                by_task[task][key] += value
        except (ET.ParseError, OSError, ValueError, IndexError) as error:
            errors.append(dict(path=str(relative), error=type(error).__name__))
    return dict(
        scope="Individual JUnit XML report counts, not proof of uncached execution or platform integration",
        report_files=len(reports),
        totals={key: sum(report[key] for report in reports)
                for key in ("tests", "failures", "errors", "skipped")},
        by_task=dict(sorted(by_task.items())), reports=reports, parse_errors=errors,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-reports", action="store_true")
    args = parser.parse_args()
    result = summarize(args.root.resolve())
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return int(bool(result["parse_errors"] or (args.require_reports and not result["report_files"])))


if __name__ == "__main__":
    sys.exit(main())
