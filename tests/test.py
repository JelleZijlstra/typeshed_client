from pathlib import Path
import typeshed_client
from unittest import mock
import unittest

TEST_TYPESHED = Path(__file__).parent / 'typeshed'


@mock.patch('typeshed_client.finder.find_typeshed', lambda: TEST_TYPESHED)
class TestTypeshedClient(unittest.TestCase):
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

        self.assertEqual(typeshed_client.get_stub_file('thirdpart', version=(3, 5)),
                         TEST_TYPESHED / 'third_party/3.5/thirdpart.pyi')
        self.assertEqual(typeshed_client.get_stub_file('thirdpart', version=(3, 4)),
                         TEST_TYPESHED / 'stdlib/3.4/thirdpart.pyi')


if __name__ == '__main__':
    unittest.main()
