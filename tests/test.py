from pathlib import Path
import ast
import typeshed_client
from typeshed_client.finder import (
    get_search_context,
    PythonVersion,
    get_stub_file,
    SearchContext,
)
from typeshed_client.parser import get_stub_names
from typing import Any, Set, Type, Optional
from unittest import mock
import unittest

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
        self.assertEqual(
            set(names.keys()),
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
        self.assertEqual(set(cls_names.keys()), {"attr", "method"})
        self.check_nameinfo(cls_names, "attr", ast.AnnAssign)
        self.check_nameinfo(cls_names, "method", ast.FunctionDef)

    def test_starimport(self) -> None:
        ctx = get_context((3, 5))
        names = get_stub_names("starimport", search_context=ctx)
        self.assertEqual(set(names.keys()), {"public"})
        self.check_nameinfo(names, "public", typeshed_client.ImportedName)
        path = typeshed_client.ModulePath(("imported",))
        self.assertEqual(
            names["public"].ast, typeshed_client.ImportedName(path, "public")
        )

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
                self.assertEqual(set(names.keys()), {"f", "overloads"})
                self.check_nameinfo(names, "f", typeshed_client.ImportedName)
                path = typeshed_client.ModulePath(("subdir", "overloads"))
                self.assertEqual(
                    names["f"].ast, typeshed_client.ImportedName(path, "f")
                )

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
        self.assertEqual(set(info.keys()), names | {"sys"})

    def test_top_level_assert(self) -> None:
        ctx = get_context((3, 6), "flat")
        info = get_stub_names("top_level_assert", search_context=ctx)
        self.assertEqual(set(info.keys()), set())
        ctx = get_context((3, 6), "linux")
        info = get_stub_names("top_level_assert", search_context=ctx)
        self.assertEqual(set(info.keys()), {"x", "sys"})

    def test_overloads(self) -> None:
        names = get_stub_names("overloads", search_context=get_context((3, 5)))
        self.assertEqual(set(names.keys()), {"overload", "overloaded", "OverloadClass"})
        self.check_nameinfo(names, "overloaded", typeshed_client.OverloadedName)
        definitions = names["overloaded"].ast.definitions
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIsInstance(defn, ast.FunctionDef)

        classdef = names["OverloadClass"]
        self.assertIsInstance(classdef.ast, ast.ClassDef)
        children = classdef.child_nodes
        self.assertEqual(set(children.keys()), {"overloaded"})
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


class IntegrationTest(unittest.TestCase):
    """Tests that all files in typeshed are parsed without error."""

    fake_path = typeshed_client.ModulePath(("some", "module"))

    def test(self) -> None:
        ctx = get_search_context()
        for module_name, module_path in typeshed_client.get_all_stub_files(ctx):
            with self.subTest(path=module_name):
                ast = typeshed_client.get_stub_ast(module_name, search_context=ctx)
                typeshed_client.parser.parse_ast(ast, ctx, self.fake_path)


if __name__ == "__main__":
    unittest.main()
