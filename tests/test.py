from pathlib import Path
from typed_ast import ast3
import typeshed_client
from typing import Any, Set, Tuple, Type
from unittest import mock
import unittest

TEST_TYPESHED = Path(__file__).parent / 'typeshed'


@mock.patch('typeshed_client.finder.find_typeshed', lambda: TEST_TYPESHED)
class TestFinder(unittest.TestCase):
    def test_get_stub_file(self) -> None:
        self.assertEqual(typeshed_client.get_stub_file('lib'), TEST_TYPESHED / 'stdlib/3.5/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(3, 6)),
                         TEST_TYPESHED / 'stdlib/3.5/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(3, 5)),
                         TEST_TYPESHED / 'stdlib/3.5/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(3, 4)),
                         TEST_TYPESHED / 'stdlib/3.4/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(3, 3)),
                         TEST_TYPESHED / 'stdlib/3.3/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(3, 2)),
                         TEST_TYPESHED / 'stdlib/3/lib.pyi')
        self.assertEqual(typeshed_client.get_stub_file('lib', version=(2, 7)),
                         TEST_TYPESHED / 'stdlib/2/lib.pyi')
        for version in ((2, 7), (3, 3), (3, 4), (3, 5), (3, 6)):
            self.assertEqual(typeshed_client.get_stub_file('shared', version=version),
                             TEST_TYPESHED / 'stdlib/2and3/shared.pyi')

    def test_third_party(self) -> None:
        self.assertEqual(typeshed_client.get_stub_file('thirdpart', version=(3, 5)),
                         TEST_TYPESHED / 'third_party/3.5/thirdpart.pyi')
        self.assertEqual(typeshed_client.get_stub_file('thirdpart', version=(3, 4)),
                         TEST_TYPESHED / 'stdlib/3.4/thirdpart.pyi')

    def test_subdir(self) -> None:
        self.assertEqual(typeshed_client.get_stub_file('subdir', version=(3, 5)),
                         TEST_TYPESHED / 'stdlib/3/subdir/__init__.pyi')


@mock.patch('typeshed_client.finder.find_typeshed', lambda: TEST_TYPESHED)
class TestParser(unittest.TestCase):
    def test_get_stub_names(self) -> None:
        names = typeshed_client.get_stub_names('simple', version=(3, 5))
        self.assertEqual(set(names.keys()), {
            'var', 'old_var', 'func', 'async_func', 'Cls', '_private',
            'exported', 'unexported', 'other', 'multiple', 'assignment', 'new_name'
        })

        # Simple assignments
        self.check_nameinfo(names, 'var', ast3.AnnAssign)
        self.check_nameinfo(names, 'old_var', ast3.Assign)
        self.check_nameinfo(names, '_private', ast3.AnnAssign, is_exported=False)
        self.check_nameinfo(names, 'multiple', ast3.Assign)
        self.check_nameinfo(names, 'assignment', ast3.Assign)

        # Imports
        path = typeshed_client.ModulePath(('other',))
        self.check_nameinfo(names, 'other', typeshed_client.ImportedName, is_exported=False)
        self.assertEqual(names['other'].ast, typeshed_client.ImportedName(path))
        self.check_nameinfo(names, 'exported', typeshed_client.ImportedName)
        self.assertEqual(names['exported'].ast, typeshed_client.ImportedName(path, 'exported'))
        self.check_nameinfo(names, 'unexported', typeshed_client.ImportedName, is_exported=False)
        self.assertEqual(names['unexported'].ast, typeshed_client.ImportedName(path, 'unexported'))
        self.check_nameinfo(names, 'new_name', typeshed_client.ImportedName)
        self.assertEqual(names['new_name'].ast, typeshed_client.ImportedName(path, 'renamed'))

        # Functions
        self.check_nameinfo(names, 'func', ast3.FunctionDef)
        self.check_nameinfo(names, 'async_func', ast3.AsyncFunctionDef)

        # Classes
        self.check_nameinfo(names, 'Cls', ast3.ClassDef, has_child_nodes=True)
        cls_names = names['Cls'].child_nodes
        self.assertEqual(set(cls_names.keys()), {'attr', 'method'})
        self.check_nameinfo(cls_names, 'attr', ast3.AnnAssign)
        self.check_nameinfo(cls_names, 'method', ast3.FunctionDef)

    def check_nameinfo(self, names: typeshed_client.NameDict, name: str, ast_type: Type[Any], *,
                       is_exported: bool = True, has_child_nodes: bool = False) -> None:
        info = names[name]
        self.assertEqual(info.name, name)
        self.assertEqual(info.is_exported, is_exported)
        if has_child_nodes:
            self.assertIsNotNone(info.child_nodes)
        else:
            self.assertIsNone(info.child_nodes)
        self.assertIsInstance(info.ast, ast_type)

    def test_conditions(self) -> None:
        self.check_conditions({'windows', 'async_generator', 'new_stuff'}, platform='win32')
        self.check_conditions({'apples', 'async_generator', 'new_stuff'}, platform='darwin')
        self.check_conditions({'penguins', 'async_generator', 'new_stuff'}, platform='linux')
        self.check_conditions({'penguins', 'async_generator', 'new_stuff'}, version=(3, 6))
        self.check_conditions({'penguins', 'typing', 'new_stuff'}, version=(3, 5))
        self.check_conditions({'penguins', 'asyncio', 'new_stuff'}, version=(3, 4))
        self.check_conditions({'penguins', 'yield_from', 'new_stuff'}, version=(3, 3))
        self.check_conditions({'penguins', 'ages_long_past', 'new_stuff'}, version=(3, 2))
        self.check_conditions({'penguins', 'ages_long_past', 'old_stuff'}, version=(2, 7))

    def check_conditions(self, names: Set[str], *, version: Tuple[int, int] = (3, 6),
                         platform: str = 'linux') -> None:
        info = typeshed_client.get_stub_names('conditions', version=version, platform=platform)
        self.assertEqual(set(info.keys()), names | {'sys'})

    def test_overloads(self) -> None:
        names = typeshed_client.get_stub_names('overloads', version=(3, 5))
        self.assertEqual(set(names.keys()), {'overload', 'overloaded'})
        self.check_nameinfo(names, 'overloaded', typeshed_client.OverloadedName)
        definitions = names['overloaded'].ast.definitions
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIsInstance(defn, ast3.FunctionDef)


if __name__ == '__main__':
    unittest.main()
