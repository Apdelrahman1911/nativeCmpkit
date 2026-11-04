"""New exact reporter-manifest source controls; no project imports or native work.

Only the owning reporter-admission AST slice and existing DTD-refusing builder
are executed when explicitly selected. Old eight, new eighteen, and batch100's
fourteen accepted method bodies are neither imported nor selected here.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

TREE = Path(os.environ.get("IO_REPORTER_MANIFEST_UNION_TREE", Path(__file__).resolve().parents[2])).resolve()
MANIFEST = "calf-io/src/androidDeviceTest/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"
NAMED_CALLER = "com.mohamedrejeb.calf.io.AndroidIoSystemTreeGrantActivity"


def owning_reporter_guard():
    """Copy one exact owning reporter block, not a replacement validator."""
    helper = TREE / "scripts/ci/android_io_documents.py"
    syntax = ast.parse(helper.read_text(encoding="utf-8"))
    functions = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == "source_contract"]
    if len(functions) != 1:
        raise AssertionError("One owning IO source contract is required")
    body = functions[0].body
    starts = [index for index, node in enumerate(body) if isinstance(node, ast.Assign) and
              any(isinstance(target, ast.Name) and target.id == "reporter" for target in node.targets)]
    ends = [index for index, node in enumerate(body) if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Name) and target.id == "paths" for target in node.targets)]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise AssertionError("One complete owning reporter block through its FileProvider gate is required")
    wrapper = ast.parse("def reporter_model(payload):\n    texts = {MANIFEST: payload.decode('utf-8')}\n").body[0]
    wrapper.body += deepcopy(body[starts[0]:ends[0]])
    required = ("PACKAGE", "PERMISSION", "ANDROID")
    constants = []
    for name in required:
        selected = [node for node in syntax.body if isinstance(node, ast.Assign) and
                    any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
        if len(selected) != 1:
            raise AssertionError("One owning reporter constant is required")
        constants += selected
    require = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == "require"]
    if len(require) != 1:
        raise AssertionError("One unchanged owning refusal function is required")
    library = ast.parse((TREE / "scripts/ci/library_tests.py").read_text(encoding="utf-8"))
    builders = [node for node in library.body if isinstance(node, ast.ClassDef) and node.name == "NoDtdBuilder"]
    if len(builders) != 1:
        raise AssertionError("The existing DTD-refusing parser must remain owning")
    builder_env = {"ET": ET}
    exec(compile(ast.fix_missing_locations(ast.Module(body=deepcopy(builders), type_ignores=[])),
                 "selected-owning-dtd-builder", "exec"), builder_env)
    env = {"ET": ET, "MANIFEST": MANIFEST,
           "lt": SimpleNamespace(NoDtdBuilder=builder_env["NoDtdBuilder"])}
    nodes = deepcopy(constants + require) + [wrapper]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(helper), "exec"), env)
    return env["reporter_model"]


def owning_reporter_fixture(payload):
    """Execute only the exact new pure source inverse, then the old parser stage."""
    syntax = ast.parse((TREE / "scripts/ci/android_io_documents.py").read_text(encoding="utf-8"))
    names = ("REMOTE_REPORTER_SHA256", "REMOTE_REPORTER_FRAGMENTS")
    constants = []
    for name in names:
        matches = [node for node in syntax.body if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
        if len(matches) != 1:
            raise AssertionError("One exact remote reporter fixture constant is required")
        constants += matches
    functions = []
    for name in ("require", "normalize_remote_reporter_source"):
        matches = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == name]
        if len(matches) != 1:
            raise AssertionError("One exact pure remote reporter fixture source function is required")
        functions += matches
    env = {"hashlib": hashlib}
    exec(compile(ast.fix_missing_locations(ast.Module(body=deepcopy(constants + functions), type_ignores=[])),
                 "selected-owning-remote-reporter-source-inverse-only", "exec"), env)
    return env["normalize_remote_reporter_source"](payload)


class ReporterManifestUnionSourceControls(unittest.TestCase):
    def setUp(self):
        self.guard = owning_reporter_guard()
        self.union = ET.fromstring(owning_reporter_fixture((TREE / MANIFEST).read_bytes()))
        self.prior = deepcopy(self.union)
        queries = self.prior.find("queries")
        if [node.tag for node in queries] != ["package", "provider", "intent"]:
            raise AssertionError("Controls require the exact currently integrated union fixture")
        queries.remove(queries[2])
        queries.remove(queries[1])
        app = self.prior.find("application")
        named = [node for node in app.findall("activity") if node.get(ANDROID + "name") == NAMED_CALLER]
        if len(named) != 1:
            raise AssertionError("Controls require the exact new caller, not an invented component")
        app.remove(named[0])

    def refused(self, root):
        with self.assertRaises(ValueError):
            self.guard(ET.tostring(root))

    def query(self, root, tag):
        return root.find("queries/" + tag)

    def named(self, root):
        return next(node for node in root.findall("application/activity")
                    if node.get(ANDROID + "name") == NAMED_CALLER)

    def test_complete_prior_and_exact_named_union_are_source_admitted_without_native_claims(self):
        for name, root in (("complete-prior", self.prior), ("complete-union", self.union)):
            with self.subTest(shape=name):
                self.assertIsNone(self.guard(ET.tostring(root)))

    def test_partial_query_pairs_and_query_caller_hybrids_cannot_pass(self):
        for remove in (("provider",), ("intent",), ("provider", "intent")):
            root = deepcopy(self.union)
            for tag in remove:
                root.find("queries").remove(self.query(root, tag))
            with self.subTest(missing_queries=remove):
                self.refused(root)
        root = deepcopy(self.union)
        root.find("application").remove(self.named(root))
        self.refused(root)
        for tag in ("provider", "intent"):
            root = deepcopy(self.prior)
            root.find("queries").append(deepcopy(self.query(self.union, tag)))
            with self.subTest(lone_query=tag):
                self.refused(root)

    def test_extra_duplicate_missing_reordered_or_unrecognized_queries_refuse(self):
        for tag in ("package", "provider", "intent", "unreviewed"):
            root = deepcopy(self.union)
            root.find("queries").append(deepcopy(self.query(self.union, tag)) if tag != "unreviewed" else ET.Element(tag))
            with self.subTest(extra=tag):
                self.refused(root)
        for index in range(3):
            root = deepcopy(self.union)
            root.find("queries").remove(root.find("queries")[index])
            with self.subTest(missing=index):
                self.refused(root)
        root = deepcopy(self.union)
        queries = root.find("queries")
        queries[:] = list(reversed(queries))
        self.refused(root)
        root = deepcopy(self.union)
        root.append(deepcopy(root.find("queries")))
        self.refused(root)

    def test_query_container_package_and_provider_attributes_or_nested_entries_refuse(self):
        for shape in (self.prior, self.union):
            for path in ("queries", "queries/package"):
                root = deepcopy(shape)
                root.find(path).set(ANDROID + "unreviewed", "true")
                with self.subTest(path=path, query_count=len(shape.find("queries"))):
                    self.refused(root)
            root = deepcopy(shape)
            ET.SubElement(root.find("queries/package"), "package", {ANDROID + "name": "foreign.package"})
            self.refused(root)
        for field in ("name", "exported", "permission", "readPermission", "writePermission", "unreviewed"):
            root = deepcopy(self.union)
            self.query(root, "provider").set(ANDROID + field, "unreviewed")
            with self.subTest(provider_attribute=field):
                self.refused(root)
        root = deepcopy(self.union)
        ET.SubElement(self.query(root, "provider"), "intent-filter")
        self.refused(root)

    def test_system_provider_authorities_are_one_exact_source_bound_string(self):
        expected = "media;com.android.externalstorage.documents;com.android.providers.downloads.documents"
        variants = ("media", expected + ";foreign.documents", expected + ";media", expected.replace("media;", ""),
                    ";".join(reversed(expected.split(";"))), expected.replace("documents", "documents.*"), " " + expected)
        for authorities in variants:
            root = deepcopy(self.union)
            self.query(root, "provider").set(ANDROID + "authorities", authorities)
            with self.subTest(authorities=authorities):
                self.refused(root)

    def test_open_tree_visibility_requires_only_the_exact_action_and_no_category_data_or_attributes(self):
        for action in ("android.intent.action.OPEN_DOCUMENT", "android.intent.action.GET_CONTENT", "foreign.ACTION"):
            root = deepcopy(self.union)
            root.find("queries/intent/action").set(ANDROID + "name", action)
            with self.subTest(action=action):
                self.refused(root)
        for path in ("queries/intent", "queries/intent/action"):
            root = deepcopy(self.union)
            root.find(path).set(ANDROID + "unreviewed", "true")
            self.refused(root)
        for tag in ("action", "category", "data", "unreviewed"):
            root = deepcopy(self.union)
            ET.SubElement(self.query(root, "intent"), tag, {ANDROID + "name": "unreviewed"})
            with self.subTest(extra_intent_child=tag):
                self.refused(root)
        root = deepcopy(self.union)
        ET.SubElement(root.find("queries/intent/action"), "unreviewed")
        self.refused(root)

    def test_named_caller_has_only_exact_name_nonexported_theme_and_no_extra_attributes(self):
        for field, value in (("name", NAMED_CALLER + "Foreign"), ("exported", "true"),
                             ("theme", "@android:style/Theme.DeviceDefault"), ("process", ":foreign"),
                             ("permission", "foreign.PERMISSION"), ("enabled", "true"), ("enabled", "false"),
                             ("grantUriPermissions", "true"), ("taskAffinity", "foreign"), ("unreviewed", "true")):
            root = deepcopy(self.union)
            self.named(root).set(ANDROID + field, value)
            with self.subTest(field=field, value=value):
                self.refused(root)
        for field in ("name", "exported", "theme"):
            root = deepcopy(self.union)
            del self.named(root).attrib[ANDROID + field]
            with self.subTest(missing_attribute=field):
                self.refused(root)

    def test_named_caller_cannot_gain_children_duplicates_foreign_components_or_old_mode_admission(self):
        for tag in ("intent-filter", "meta-data", "provider", "unreviewed"):
            root = deepcopy(self.union)
            ET.SubElement(self.named(root), tag)
            with self.subTest(child=tag):
                self.refused(root)
        root = deepcopy(self.union)
        root.find("application").append(deepcopy(self.named(root)))
        self.refused(root)
        root = deepcopy(self.prior)
        root.find("application").append(deepcopy(self.named(self.union)))
        self.refused(root)
        root = deepcopy(self.union)
        ET.SubElement(root.find("application"), "activity", {ANDROID + "name": "foreign.Activity", ANDROID + "exported": "false"})
        self.refused(root)

    def test_original_single_control_permission_and_reporter_uid_process_refusals_remain(self):
        for shape in (self.prior, self.union):
            for tag in ("uses-permission", "uses-permission-sdk-23"):
                root = deepcopy(shape)
                ET.SubElement(root, tag, {ANDROID + "name": "android.permission.MANAGE_DOCUMENTS"})
                with self.subTest(tag=tag, query_count=len(shape.find("queries"))):
                    self.refused(root)
            for field in ("sharedUserId", "sharedUserMaxSdkVersion"):
                root = deepcopy(shape)
                root.set(ANDROID + field, "unreviewed")
                self.refused(root)
            for field in ("process", "permission"):
                root = deepcopy(shape)
                root.find("application").set(ANDROID + field, "unreviewed")
                self.refused(root)

    def test_original_grant_callers_and_bookmark_client_stay_private_with_no_extra_routes(self):
        for shape in (self.prior, self.union):
            old = [node for node in shape.findall("application/activity") if node.get(ANDROID + "name") != NAMED_CALLER]
            self.assertEqual(2, len(old))
            for original in old:
                for field, value in (("exported", "true"), ("permission", "foreign.PERMISSION"),
                                     ("process", ":foreign"), ("enabled", "false"), ("name", "foreign.Activity")):
                    root = deepcopy(shape)
                    node = next(node for node in root.findall("application/activity")
                                if node.get(ANDROID + "name") == original.get(ANDROID + "name"))
                    node.set(ANDROID + field, value)
                    with self.subTest(caller=original.get(ANDROID + "name"), field=field):
                        self.refused(root)
                root = deepcopy(shape)
                node = next(node for node in root.findall("application/activity")
                            if node.get(ANDROID + "name") == original.get(ANDROID + "name"))
                ET.SubElement(node, "intent-filter")
                self.refused(root)
            for field, value in (("exported", "true"), ("process", ":foreign"),
                                 ("permission", "foreign.PERMISSION"), ("enabled", "false"), ("name", "foreign.Service")):
                root = deepcopy(shape)
                root.find("application/service").set(ANDROID + field, value)
                self.refused(root)
            root = deepcopy(shape)
            ET.SubElement(root.find("application/service"), "intent-filter")
            self.refused(root)

    def test_original_fileprovider_fixed_authority_process_grant_and_path_metadata_refusals_remain(self):
        for shape in (self.prior, self.union):
            for field, value in (("name", "foreign.Provider"), ("authorities", "foreign.documents"),
                                 ("exported", "true"), ("process", ":foreign"), ("grantUriPermissions", "false"),
                                 ("permission", "foreign.PERMISSION"), ("readPermission", "foreign.PERMISSION"),
                                 ("writePermission", "foreign.PERMISSION"), ("enabled", "false")):
                root = deepcopy(shape)
                root.find("application/provider").set(ANDROID + field, value)
                with self.subTest(field=field, query_count=len(shape.find("queries"))):
                    self.refused(root)
            for field, value in (("name", "foreign.PATHS"), ("resource", "@xml/foreign_paths")):
                root = deepcopy(shape)
                root.find("application/provider/meta-data").set(ANDROID + field, value)
                self.refused(root)
            root = deepcopy(shape)
            ET.SubElement(root.find("application/provider/meta-data"), "grant-uri-permission")
            self.refused(root)
            root = deepcopy(shape)
            ET.SubElement(root.find("application/provider"), "grant-uri-permission")
            self.refused(root)

    def test_existing_dtd_refusal_and_malformed_xml_do_not_become_union_admission(self):
        for payload in (b"", b"not XML", b"<!DOCTYPE manifest><manifest/>",
                        b'<!DOCTYPE manifest [<!ENTITY x "unreviewed">]><manifest>&x;</manifest>'):
            with self.subTest(payload=payload), self.assertRaises((ValueError, ET.ParseError)):
                self.guard(payload)


if __name__ == "__main__":
    unittest.main()
