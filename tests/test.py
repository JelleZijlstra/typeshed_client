import ast
import unittest
from pathlib import Path
from typing import Any, Optional, Set, Type
from unittest import mock

import typeshed_client
from typeshed_client.finder import (
    ModulePath,
    PythonVersion,
    SearchContext,
    get_search_context,
    get_stub_file,
)
from typeshed_client.parser import get_stub_names

TEST_TYPESHED = Path(__file__).parent / "typeshed"
PACKAGES = Path(__file__).parent / "site-packages"


def get_context(version: PythonVersion, platform: str = "linux") -> SearchContext:
    return get_search_context(
        version=version,
        typeshed=TEST_TYPESHED,
        search_path=[PACKAGES],
        platform=platform,
    )


class TestFinder(unittest.TestCase):
    def check(
        self, name: str, version: PythonVersion, expected: Optional[Path]
    ) -> None:
        ctx = get_context(version)
        self.assertEqual(get_stub_file(name, search_context=ctx), expected)

    def test_get_stub_file(self) -> None:
        self.check("lib", (3, 6), TEST_TYPESHED / "lib.pyi")
        self.check("lib", (3, 5), TEST_TYPESHED / "lib.pyi")
        self.check("lib", (2, 7), TEST_TYPESHED / "@python2/lib.pyi")

        self.check("py2only", (3, 5), None)
        self.check("py2only", (2, 7), TEST_TYPESHED / "@python2/py2only.pyi")

        self.check("new37", (3, 6), None)
        self.check("new37", (3, 7), TEST_TYPESHED / "new37.pyi")

        self.check("subdir", (3, 6), TEST_TYPESHED / "subdir/__init__.pyi")
        self.check("subdir.overloads", (3, 7), TEST_TYPESHED / "subdir/overloads.pyi")
        self.check("subdir", (2, 7), TEST_TYPESHED / "@python2/subdir.pyi")
        self.check("subdir.overloads", (2, 7), None)

    def test_third_party(self) -> None:
        self.check("thirdparty", (3, 6), PACKAGES / "thirdparty-stubs/__init__.pyi")
        self.check("nostubs", (3, 6), PACKAGES / "nostubs/__init__.pyi")

    def test_get_all_stub_files(self) -> None:
        all_stubs = typeshed_client.get_all_stub_files(get_context((2, 7)))
        self.assertEqual(
            set(all_stubs),
            {
                ("thirdparty", PACKAGES / "thirdparty-stubs/__init__.pyi"),
                ("nostubs", PACKAGES / "nostubs/__init__.pyi"),
                ("subdir", TEST_TYPESHED / "@python2/subdir.pyi"),
                ("py2only", TEST_TYPESHED / "@python2/py2only.pyi"),
                ("lib", TEST_TYPESHED / "@python2/lib.pyi"),
                ("conditions", TEST_TYPESHED / "conditions.pyi"),
                ("top_level_assert", TEST_TYPESHED / "top_level_assert.pyi"),
            },
        )


class TestParser(unittest.TestCase):
    def test_get_stub_names(self) -> None:
        ctx = get_context((3, 5))
        names = get_stub_names("simple", search_context=ctx)
        assert names is not None
        self.assertEqual(
            set(names),
            {
                "var",
                "old_var",
                "func",
                "async_func",
                "Cls",
                "_private",
                "exported",
                "unexported",
                "other",
                "multiple",
                "assignment",
                "new_name",
                "_made_private",
            },
        )

        # Simple assignments
        self.check_nameinfo(names, "var", ast.AnnAssign)
        self.check_nameinfo(names, "old_var", ast.Assign)
        self.check_nameinfo(names, "_private", ast.AnnAssign, is_exported=False)
        self.check_nameinfo(names, "multiple", ast.Assign)
        self.check_nameinfo(names, "assignment", ast.Assign)

        # Imports
        path = typeshed_client.ModulePath(("other",))
        self.check_nameinfo(
            names, "other", typeshed_client.ImportedName, is_exported=False
        )
        self.assertEqual(names["other"].ast, typeshed_client.ImportedName(path))
        self.check_nameinfo(names, "exported", typeshed_client.ImportedName)
        self.assertEqual(
            names["exported"].ast, typeshed_client.ImportedName(path, "exported")
        )
        self.check_nameinfo(
            names, "unexported", typeshed_client.ImportedName, is_exported=False
        )
        self.assertEqual(
            names["unexported"].ast, typeshed_client.ImportedName(path, "unexported")
        )
        self.check_nameinfo(names, "new_name", typeshed_client.ImportedName)
        self.assertEqual(
            names["new_name"].ast, typeshed_client.ImportedName(path, "renamed")
        )
        self.check_nameinfo(
            names, "_made_private", typeshed_client.ImportedName, is_exported=False
        )
        self.assertEqual(
            names["_made_private"].ast,
            typeshed_client.ImportedName(path, "made_private"),
        )

        # Functions
        self.check_nameinfo(names, "func", ast.FunctionDef)
        self.check_nameinfo(names, "async_func", ast.AsyncFunctionDef)

        # Classes
        self.check_nameinfo(names, "Cls", ast.ClassDef, has_child_nodes=True)
        cls_names = names["Cls"].child_nodes
        assert cls_names is not None
        self.assertEqual(set(cls_names), {"attr", "method"})
        self.check_nameinfo(cls_names, "attr", ast.AnnAssign)
        self.check_nameinfo(cls_names, "method", ast.FunctionDef)

    def test_starimport(self) -> None:
        ctx = get_context((3, 5))
        names = get_stub_names("starimport", search_context=ctx)
        assert names is not None
        self.assertEqual(set(names), {"public"})
        self.check_nameinfo(names, "public", typeshed_client.ImportedName)
        path = typeshed_client.ModulePath(("imported",))
        self.assertEqual(
            names["public"].ast, typeshed_client.ImportedName(path, "public")
        )

    def test_starimport_all(self) -> None:
        ctx = get_context((3, 10))
        names = get_stub_names("starimportall", search_context=ctx)
        assert names is not None
        expected = {"a", "b", "c", "f", "h", "n"}
        self.assertEqual(set(names), expected)
        for name in expected:
            self.check_nameinfo(names, name, typeshed_client.ImportedName)
            module = "tupleall" if name == "n" else "dunder_all"
            path = typeshed_client.ModulePath((module,))
            self.assertEqual(names[name].ast, typeshed_client.ImportedName(path, name))

    def test_starimport_no_dunders(self) -> None:
        ctx = get_context((3, 10))
        names = get_stub_names("importabout", search_context=ctx)
        assert names is not None
        self.assertEqual(set(names), {"x"})
        self.check_nameinfo(names, "x", typeshed_client.ImportedName)
        path = typeshed_client.ModulePath(("about",))
        self.assertEqual(names["x"].ast, typeshed_client.ImportedName(path, "x"))

    def test_dot_import(self) -> None:
        ctx = get_context((3, 5))
        for mod in (
            "subdir",
            "subdir.sibling",
            "subdir.subsubdir",
            "subdir.subsubdir.sibling",
        ):
            with self.subTest(mod):
                names = get_stub_names(mod, search_context=ctx)
                assert names is not None
                self.assertEqual(set(names), {"f", "overloads"})
                self.check_nameinfo(names, "f", typeshed_client.ImportedName)
                path = typeshed_client.ModulePath(("subdir", "overloads"))
                self.assertEqual(
                    names["f"].ast, typeshed_client.ImportedName(path, "f")
                )

    def test_try(self) -> None:
        ctx = get_context((3, 10))
        names = get_stub_names("tryexcept", search_context=ctx)
        assert names is not None
        self.assertEqual(set(names), {"np", "f", "x"})
        self.check_nameinfo(names, "np", typeshed_client.ImportedName)
        self.check_nameinfo(names, "f", ast.FunctionDef)
        self.check_nameinfo(names, "x", ast.AnnAssign)

    def check_nameinfo(
        self,
        names: typeshed_client.NameDict,
        name: str,
        ast_type: Type[Any],
        *,
        is_exported: bool = True,
        has_child_nodes: bool = False,
    ) -> None:
        info = names[name]
        self.assertEqual(info.name, name)
        self.assertEqual(info.is_exported, is_exported)
        if has_child_nodes:
            self.assertIsNotNone(info.child_nodes)
        else:
            self.assertIsNone(info.child_nodes)
        self.assertIsInstance(info.ast, ast_type)

    def test_conditions(self) -> None:
        self.check_conditions(
            {"windows", "async_generator", "new_stuff"}, platform="win32"
        )
        self.check_conditions(
            {"apples", "async_generator", "new_stuff"}, platform="darwin"
        )
        self.check_conditions(
            {"penguins", "async_generator", "new_stuff"}, platform="linux"
        )
        self.check_conditions(
            {"penguins", "async_generator", "new_stuff"}, version=(3, 6)
        )
        self.check_conditions({"penguins", "typing", "new_stuff"}, version=(3, 5))
        self.check_conditions({"penguins", "asyncio", "new_stuff"}, version=(3, 4))
        self.check_conditions({"penguins", "yield_from", "new_stuff"}, version=(3, 3))
        self.check_conditions(
            {"penguins", "ages_long_past", "new_stuff"}, version=(3, 2)
        )
        self.check_conditions(
            {"penguins", "ages_long_past", "old_stuff", "more_old_stuff"},
            version=(2, 7),
        )

    def check_conditions(
        self,
        names: Set[str],
        *,
        version: PythonVersion = (3, 6),
        platform: str = "linux",
    ) -> None:
        ctx = get_context(version, platform)
        info = get_stub_names("conditions", search_context=ctx)
        assert info is not None
        self.assertEqual(set(info), names | {"sys"})

    def test_top_level_assert(self) -> None:
        ctx = get_context((3, 6), "flat")
        info = get_stub_names("top_level_assert", search_context=ctx)
        assert info is not None
        self.assertEqual(set(info), set())
        ctx = get_context((3, 6), "linux")
        info = get_stub_names("top_level_assert", search_context=ctx)
        assert info is not None
        self.assertEqual(set(info), {"x", "sys"})

    def test_ifmypy(self) -> None:
        names = get_stub_names("ifmypy", search_context=get_context((3, 11)))
        assert names is not None
        self.assertEqual(set(names), {"MYPY", "we_are_not_mypy"})

    def test_overloads(self) -> None:
        names = get_stub_names("overloads", search_context=get_context((3, 5)))
        assert names is not None
        self.assertEqual(set(names), {"overload", "overloaded", "OverloadClass"})
        self.check_nameinfo(names, "overloaded", typeshed_client.OverloadedName)
        assert isinstance(names["overloaded"].ast, typeshed_client.OverloadedName)
        definitions = names["overloaded"].ast.definitions
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIsInstance(defn, ast.FunctionDef)

        classdef = names["OverloadClass"]
        self.assertIsInstance(classdef.ast, ast.ClassDef)
        children = classdef.child_nodes
        assert children is not None
        self.assertEqual(set(children), {"overloaded"})
        definitions = children["overloaded"].ast.definitions
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIsInstance(defn, ast.FunctionDef)


class TestResolver(unittest.TestCase):
    def test_simple(self) -> None:
        res = typeshed_client.Resolver(get_context((3, 5)))
        path = typeshed_client.ModulePath(("simple",))
        other_path = typeshed_client.ModulePath(("other",))

        self.assertIsNone(res.get_name(path, "nosuchname"))
        self.assertEqual(res.get_name(path, "other"), other_path)

        name_info = typeshed_client.NameInfo("exported", True, mock.ANY)
        resolved = res.get_name(path, "exported")
        assert isinstance(resolved, typeshed_client.ImportedInfo)
        self.assertEqual(resolved, typeshed_client.ImportedInfo(other_path, name_info))
        self.assertIsInstance(resolved.info.ast, ast.AnnAssign)

        self.assertIsInstance(res.get_name(path, "var"), typeshed_client.NameInfo)

    def test_module(self) -> None:
        res = typeshed_client.Resolver(get_context((3, 5)))
        path = typeshed_client.ModulePath(("subdir",))
        self.assertEqual(
            res.get_name(path, "overloads"),
            typeshed_client.ModulePath(("subdir", "overloads")),
        )
        path2 = typeshed_client.ModulePath(("subdir", "subsubdir", "sibling"))
        self.assertEqual(
            res.get_name(path2, "overloads"),
            typeshed_client.ModulePath(("subdir", "overloads")),
        )

    def test_dunder_all(self) -> None:
        path = typeshed_client.ModulePath(("dunder_all",))

        res = typeshed_client.Resolver(get_context((3, 5)))
        mod = res.get_module(path)
        self.assertIsNotNone(mod)
        self.assertEqual(mod.get_dunder_all(res), ["a", "b", "d", "g", "i"])

        res = typeshed_client.Resolver(get_context((3, 11)))
        mod = res.get_module(path)
        self.assertIsNotNone(mod)
        self.assertEqual(mod.get_dunder_all(res), ["a", "b", "c", "f", "h"])


class IntegrationTest(unittest.TestCase):
    """Tests that all files in typeshed are parsed without error."""

    fake_path = typeshed_client.ModulePath(("some", "module"))

    def test(self) -> None:
        ctx = get_search_context(raise_on_warnings=True)
        for module_name, module_path in typeshed_client.get_all_stub_files(ctx):
            with self.subTest(name=module_name, path=module_path):
                try:
                    ast = typeshed_client.get_stub_ast(module_name, search_context=ctx)
                except SyntaxError:
                    # idlelib for some reason ships an example stub file with a syntax error.
                    # typeshed-client should also throw a SyntaxError in this case.
                    continue
                assert ast is not None
                is_init = module_path.name == "__init__.pyi"
                typeshed_client.parser.parse_ast(
                    ast, ctx, ModulePath(tuple(module_name.split("."))), is_init=is_init
                )


if __name__ == "__main__":
    unittest.main()
