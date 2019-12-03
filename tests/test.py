from functools import partial
import os
from pathlib import Path
from typed_ast import ast3
import typeshed_client
from typing import Any, Set, Tuple, Type
from unittest import mock
import unittest

TEST_TYPESHED = Path(__file__).parent / "typeshed"

get_stub_file = partial(typeshed_client.get_stub_file, typeshed_dir=TEST_TYPESHED)
get_stub_names = partial(typeshed_client.get_stub_names, typeshed_dir=TEST_TYPESHED)


class TestFinder(unittest.TestCase):
    def test_get_stub_file(self) -> None:
        self.assertEqual(get_stub_file("lib"), TEST_TYPESHED / "stdlib/3.5/lib.pyi")
        self.assertEqual(
            get_stub_file("lib", version=(3, 6)), TEST_TYPESHED / "stdlib/3.5/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("lib", version=(3, 5)), TEST_TYPESHED / "stdlib/3.5/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("lib", version=(3, 4)), TEST_TYPESHED / "stdlib/3.4/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("lib", version=(3, 3)), TEST_TYPESHED / "stdlib/3.3/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("lib", version=(3, 2)), TEST_TYPESHED / "stdlib/3/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("lib", version=(2, 7)), TEST_TYPESHED / "stdlib/2/lib.pyi"
        )
        self.assertEqual(
            get_stub_file("subdir.overloads", version=(3, 6)),
            TEST_TYPESHED / "stdlib/3/subdir/overloads.pyi",
        )
        self.assertEqual(
            get_stub_file("overloads", version=(3, 6)),
            TEST_TYPESHED / "stdlib/3/overloads.pyi",
        )
        for version in ((2, 7), (3, 3), (3, 4), (3, 5), (3, 6)):
            self.assertEqual(
                get_stub_file("shared", version=version),
                TEST_TYPESHED / "stdlib/2and3/shared.pyi",
            )

    def test_third_party(self) -> None:
        self.assertEqual(
            get_stub_file("thirdpart", version=(3, 5)),
            TEST_TYPESHED / "third_party/3.5/thirdpart.pyi",
        )
        self.assertEqual(
            get_stub_file("thirdpart", version=(3, 4)),
            TEST_TYPESHED / "stdlib/3.4/thirdpart.pyi",
        )

    def test_subdir(self) -> None:
        self.assertEqual(
            get_stub_file("subdir", version=(3, 5)),
            TEST_TYPESHED / "stdlib/3/subdir/__init__.pyi",
        )

    def test_get_all_stub_files(self) -> None:
        all_stubs = typeshed_client.get_all_stub_files(
            version=(2, 7), typeshed_dir=TEST_TYPESHED
        )
        self.assertEqual(
            set(all_stubs),
            {
                ("lib", TEST_TYPESHED / "stdlib/2/lib.pyi"),
                ("conditions", TEST_TYPESHED / "stdlib/2and3/conditions.pyi"),
                ("shared", TEST_TYPESHED / "stdlib/2and3/shared.pyi"),
            },
        )


class TestParser(unittest.TestCase):
    def test_get_stub_names(self) -> None:
        names = get_stub_names("simple", version=(3, 5))
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
        self.check_nameinfo(names, "var", ast3.AnnAssign)
        self.check_nameinfo(names, "old_var", ast3.Assign)
        self.check_nameinfo(names, "_private", ast3.AnnAssign, is_exported=False)
        self.check_nameinfo(names, "multiple", ast3.Assign)
        self.check_nameinfo(names, "assignment", ast3.Assign)

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
        self.check_nameinfo(names, "func", ast3.FunctionDef)
        self.check_nameinfo(names, "async_func", ast3.AsyncFunctionDef)

        # Classes
        self.check_nameinfo(names, "Cls", ast3.ClassDef, has_child_nodes=True)
        cls_names = names["Cls"].child_nodes
        self.assertEqual(set(cls_names.keys()), {"attr", "method"})
        self.check_nameinfo(cls_names, "attr", ast3.AnnAssign)
        self.check_nameinfo(cls_names, "method", ast3.FunctionDef)

    def test_starimport(self) -> None:
        names = get_stub_names("starimport", version=(3, 5))
        self.assertEqual(set(names.keys()), {"public"})
        self.check_nameinfo(names, "public", typeshed_client.ImportedName)
        path = typeshed_client.ModulePath(("imported",))
        self.assertEqual(
            names["public"].ast, typeshed_client.ImportedName(path, "public")
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
        version: Tuple[int, int] = (3, 6),
        platform: str = "linux",
    ) -> None:
        info = get_stub_names("conditions", version=version, platform=platform)
        self.assertEqual(set(info.keys()), names | {"sys"})

    def test_overloads(self) -> None:
        names = get_stub_names("overloads", version=(3, 5))
        self.assertEqual(set(names.keys()), {"overload", "overloaded"})
        self.check_nameinfo(names, "overloaded", typeshed_client.OverloadedName)
        definitions = names["overloaded"].ast.definitions
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIsInstance(defn, ast3.FunctionDef)


class TestResolver(unittest.TestCase):
    def test_simple(self) -> None:
        res = typeshed_client.Resolver(version=(3, 5), typeshed_dir=TEST_TYPESHED)
        path = typeshed_client.ModulePath(("simple",))
        other_path = typeshed_client.ModulePath(("other",))

        self.assertIsNone(res.get_name(path, "nosuchname"))
        self.assertEqual(res.get_name(path, "other"), other_path)

        name_info = typeshed_client.NameInfo("exported", True, mock.ANY)
        resolved = res.get_name(path, "exported")
        self.assertEqual(resolved, typeshed_client.ImportedInfo(other_path, name_info))
        self.assertIsInstance(resolved.info.ast, ast3.AnnAssign)

        self.assertIsInstance(res.get_name(path, "var"), typeshed_client.NameInfo)


class IntegrationTest(unittest.TestCase):
    """Tests that all files in typeshed are parsed without error."""

    fake_env = typeshed_client.parser.Env(
        (3, 6), "linux", typeshed_client.finder.find_typeshed()
    )
    fake_path = typeshed_client.ModulePath(("some", "module"))

    def test(self):
        typeshed_root = typeshed_client.finder.find_typeshed()
        self.assertTrue(typeshed_root.is_dir())
        for dirpath, _, filenames in os.walk(typeshed_root):
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix != ".pyi":
                    continue
                with self.subTest(path=path):
                    self.check_path(path)

    def check_path(self, path: Path) -> None:
        ast = typeshed_client.finder.parse_stub_file(path)
        typeshed_client.parser.parse_ast(ast, self.fake_env, self.fake_path)


if __name__ == "__main__":
    unittest.main()
