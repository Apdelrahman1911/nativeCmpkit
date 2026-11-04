# SPDX-License-Identifier: Apache-2.0
"""Read finite matrix aliases without importing native controllers.

This is an offline source-fixture reader, not a workflow/native test selector.
Two original helpers use literal PROFILE/MODULE/FOCUS declarations. The sole new
Share recovery helper uses two exact, source-backed one-hop forwards plus its
literal MODULE. Unknown aliases, expressions, imports and duplicates fail.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from types import SimpleNamespace


_DECLARATIONS = {
    "calendar_native": (
        "ios_calendar_native_focus",
        {"PROFILE": "permissions-ios-calendar-configuration",
         "MODULE": "calf-permissions/calendar",
         "FOCUS": "permission-ios-calendar-configuration"},
    ),
    "macos_share_native": (
        "macos_share_native_focus",
        {"PROFILE": "macos-share-lifecycle",
         "MODULE": "calf-share",
         "FOCUS": "macos-share-coroutine-lifecycle"},
    ),
}
_FORWARDED_DECLARATIONS = {
    "share_missing": (
        "macos_share_missing_ci",
        {"PROFILE": "macos-share-missing-lifecycle", "MODULE": "calf-share",
         "FOCUS": "macos-share-timeout-retention-recovery"},
        "recovery", "macos_share_missing_only",
        {"PROFILE": "JNI_PROFILE", "FOCUS": "JNI_FOCUS"},
    ),
}
MAX_DECLARATION_BYTES = 131072


def _exact_import(tree: ast.Module, alias: str, module: str) -> None:
    imports = [item for node in tree.body if isinstance(node, ast.Import)
               for item in node.names if item.asname == alias or item.name == alias]
    if (len(imports) != 1 or imports[0].name != module or imports[0].asname != alias or
            any(isinstance(node, ast.ImportFrom) and any(item.asname == alias or item.name == alias
                for item in node.names) for node in tree.body)):
        raise AssertionError("An exact known declarative matrix import is required: " + alias)
    if any(isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Store) and
           (node.id if isinstance(node, ast.Name) else ast.unparse(node)).split(".")[0] == alias
           for node in ast.walk(tree)):
        raise AssertionError("Matrix aliases must not be reassigned or mutated")


def _bounded_tree(module: str, read_source) -> ast.Module:
    source = read_source("scripts/ci/" + module + ".py")
    if not isinstance(source, str) or not source or len(source.encode("utf-8")) > MAX_DECLARATION_BYTES:
        raise AssertionError("A bounded declarative helper source is required")
    return ast.parse(source)


def _single_value(tree: ast.Module, name: str) -> ast.expr:
    declarations = [node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                    and any(isinstance(target, ast.Name) and target.id == name
                        for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))]
    if len(declarations) != 1 or not isinstance(declarations[0], ast.Assign) or len(declarations[0].targets) != 1:
        raise AssertionError("One exact native matrix declaration is required: " + name)
    return declarations[0].value


def _forwarded_aliases(matrix_tree: ast.Module, read_source) -> dict[str, SimpleNamespace]:
    result = {}
    for alias, (module, expected, upstream_alias, upstream_module, forwards) in _FORWARDED_DECLARATIONS.items():
        requested = any(isinstance(node, ast.Name) and node.id == alias or
                        isinstance(node, (ast.Import, ast.ImportFrom)) and
                        any(item.asname == alias or item.name == alias for item in node.names)
                        for node in ast.walk(matrix_tree))
        if not requested:
            continue  # Older source fixtures have no new alias or new helper dependency.
        _exact_import(matrix_tree, alias, module)
        helper = _bounded_tree(module, read_source)
        _exact_import(helper, upstream_alias, upstream_module)
        upstream = _bounded_tree(upstream_module, read_source)
        values = {}
        for name, expected_value in expected.items():
            value = _single_value(helper, name)
            if name in forwards:
                if (not isinstance(value, ast.Attribute) or not isinstance(value.value, ast.Name) or
                        value.value.id != upstream_alias or value.attr != forwards[name]):
                    raise AssertionError("Only one exact source-backed native declaration hop is allowed")
                value = _single_value(upstream, forwards[name])
            if not isinstance(value, ast.Constant) or type(value.value) is not str or value.value != expected_value:
                raise AssertionError("One exact literal native matrix declaration is required: " + alias + "." + name)
            values[name] = value.value
        result[alias] = SimpleNamespace(**values)
    return result


def native_aliases(matrix_tree: ast.Module, read_source) -> dict[str, SimpleNamespace]:
    """Qualify imports and source-backed constants; never execute helper code."""
    aliases = {}
    for alias, (module_name, expected) in _DECLARATIONS.items():
        imports = [item for node in matrix_tree.body if isinstance(node, ast.Import)
                   for item in node.names if item.asname == alias or item.name == alias]
        if (len(imports) != 1 or imports[0].name != module_name or
                imports[0].asname != alias or any(
                    isinstance(node, ast.ImportFrom) and any(
                        item.asname == alias or item.name == alias for item in node.names)
                    for node in matrix_tree.body)):
            raise AssertionError("An exact known declarative matrix import is required: " + alias)
        if any(isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Store)
               and (node.id if isinstance(node, ast.Name) else ast.unparse(node)).split(".")[0] == alias
               for node in ast.walk(matrix_tree)):
            raise AssertionError("Matrix aliases must not be reassigned or mutated")
        source = read_source("scripts/ci/" + module_name + ".py")
        if not isinstance(source, str) or not source or len(source.encode("utf-8")) > MAX_DECLARATION_BYTES:
            raise AssertionError("A bounded declarative helper source is required")
        tree = ast.parse(source)
        values = {}
        for name, value in expected.items():
            declarations = [node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                            and any(isinstance(target, ast.Name) and target.id == name
                                    for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))]
            if (len(declarations) != 1 or not isinstance(declarations[0], ast.Assign) or
                    len(declarations[0].targets) != 1 or
                    not isinstance(declarations[0].value, ast.Constant) or
                    type(declarations[0].value.value) is not str or declarations[0].value.value != value):
                raise AssertionError("One exact literal native matrix declaration is required: " + alias + "." + name)
            values[name] = declarations[0].value.value
        aliases[alias] = SimpleNamespace(**values)
    aliases.update(_forwarded_aliases(matrix_tree, read_source))
    return aliases


def literal_metadata(node: ast.AST, aliases: dict[str, SimpleNamespace]):
    """Literal-only AST evaluation with an explicit, finite attribute allowance."""
    class Resolve(ast.NodeTransformer):
        def visit_Attribute(self, attribute):
            declarations = {**_DECLARATIONS, **_FORWARDED_DECLARATIONS}
            if (not isinstance(attribute.value, ast.Name) or
                    attribute.value.id not in declarations or
                    attribute.attr not in declarations[attribute.value.id][1] or
                    attribute.value.id not in aliases):
                raise AssertionError("Unknown declarative matrix alias or attribute")
            expected = declarations[attribute.value.id][1][attribute.attr]
            value = getattr(aliases[attribute.value.id], attribute.attr, None)
            if type(value) is not str or value != expected:
                raise AssertionError("Unqualified declarative matrix alias metadata")
            return ast.copy_location(ast.Constant(value=value), attribute)

    resolved = Resolve().visit(deepcopy(node))
    try:
        for mapping in (item for item in ast.walk(resolved) if isinstance(item, ast.Dict)):
            keys = [ast.literal_eval(key) for key in mapping.keys]
            if len(keys) != len(set(keys)):
                raise AssertionError("Duplicate declarative matrix keys are prohibited")
        return ast.literal_eval(resolved)
    except (ValueError, TypeError) as error:
        raise AssertionError("Only literal finite matrix metadata may be evaluated") from error


def validate_literal_matrix_declarations(matrix_tree: ast.Module, aliases) -> None:
    """Before the old bounded matrix fixture executes, reject extra expressions."""
    def declaration(name):
        nodes = [node for node in matrix_tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
        if len(nodes) != 1:
            raise AssertionError("One exact declarative matrix mapping is required")
        return nodes[0].value

    literal_metadata(declaration("SLOTS"), aliases)
    literal_metadata(declaration("MODULE_SUBSETS"), aliases)
    profiles = declaration("PROFILES")
    if not isinstance(profiles, ast.Dict):
        raise AssertionError("A declarative profile mapping is required")
    names = [literal_metadata(key, aliases) for key in profiles.keys]
    if len(names) != len(set(names)):
        raise AssertionError("Duplicate declarative matrix profiles are prohibited")
    all_generator = ast.parse('tuple(slot["slot"] for slot in SLOTS)', mode="eval").body
    for name, value in zip(names, profiles.values):
        if name == "all":
            if ast.dump(value, include_attributes=False) != ast.dump(all_generator, include_attributes=False):
                raise AssertionError("The unchanged finite all-slot generator is required")
        else:
            literal_metadata(value, aliases)
