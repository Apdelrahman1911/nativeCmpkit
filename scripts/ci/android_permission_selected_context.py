# SPDX-License-Identifier: Apache-2.0
"""Owning inert dependency contexts for finite permission AST/source fixtures.

Only the named actual contract declarations and pure validation functions are
compiled. Process-backed planners/controllers and filesystem contract producers
are not imported or executed. These are source/model checks, never native proof.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import re
from types import SimpleNamespace

MAX_CONTEXT_SOURCE_BYTES = 65536
LIFECYCLE_SOURCE = "scripts/ci/android_permission_lifecycle_contract.py"
CALLBACK_SOURCE = "scripts/ci/android_camera_callback_native_focus.py"
LIFECYCLE_DECLARATIONS = (
    "API", "MODULE", "PACKAGE", "FIXTURE", "CLASS", "KOTLIN", "SOURCE",
    "APPLICATION_KOTLIN", "METHODS", "SPECS", "FOCUSES", "SOURCE_FILES",
)
LIFECYCLE_FUNCTIONS = (
    "require", "test_filter", "validate_request", "validate_source_receipt", "validate_plan",
)


def _selected_context(read_source, relative, declarations, functions):
    source = read_source(relative)
    if type(source) is not str or not source or len(source.encode("utf-8")) > MAX_CONTEXT_SOURCE_BYTES:
        raise ValueError("Bounded actual inert contract source required")
    tree = ast.parse(source)
    nodes = []
    for name in declarations:
        matches = [node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                   and any(isinstance(target, ast.Name) and target.id == name for target in
                       (node.targets if isinstance(node, ast.Assign) else [node.target]))]
        if (len(matches) != 1 or not isinstance(matches[0], ast.Assign) or
                len(matches[0].targets) != 1 or not isinstance(matches[0].targets[0], ast.Name)):
            raise ValueError("One exact owning inert declaration required: " + name)
        nodes.append(matches[0])
    for name in functions:
        matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   and node.name == name]
        if len(matches) != 1 or not isinstance(matches[0], ast.FunctionDef) or matches[0].decorator_list:
            raise ValueError("One undecorated owning pure contract function required: " + name)
        nodes.append(matches[0])
    env = {"hashlib": hashlib, "re": re}
    module = ast.fix_missing_locations(ast.Module(body=deepcopy(nodes), type_ignores=[]))
    exec(compile(module, "selected-inert-contract/" + relative, "exec"), env)
    return SimpleNamespace(**{name: env[name] for name in declarations + functions})


def permission_lifecycle_context(read_source):
    return _selected_context(read_source, LIFECYCLE_SOURCE, LIFECYCLE_DECLARATIONS, LIFECYCLE_FUNCTIONS)


def camera_callback_admission_context(read_source):
    return _selected_context(read_source, CALLBACK_SOURCE, ("MODULE", "FOCUS"), ("validate_discovery", "validate_api"))


def permission_spec_extension(library_tree):
    """Keep the one actual owning metadata extension; never omit the new focuses."""
    expected = ast.parse("ANDROID_PERMISSION_DEVICE_SPECS.update(permission_lifecycle.SPECS)").body[0]
    matches = [node for node in library_tree.body if isinstance(node, ast.Expr) and
               isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and
               isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == "ANDROID_PERMISSION_DEVICE_SPECS" and
               node.value.func.attr == "update"]
    if (len(matches) != 1 or ast.dump(matches[0], include_attributes=False) != ast.dump(expected, include_attributes=False)):
        raise ValueError("Exactly the owning permission lifecycle specification extension required")
    return deepcopy(matches[0])
