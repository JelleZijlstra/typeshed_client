This project aims to provide a standardized way of retrieving information from
`typeshed <https://www.github.com/python/typeshed>`_.

It's still a work in progress, and I need to do more work identifying use cases
and coming up with a good API.

Example use cases:

- Find the path to the stub file for a particular module.
- Find the names defined in a stub.
- Find the AST node that defines a particular name in a stub.

Projects for which ``typeshed_client`` could be useful include:

- Static analyzers that want to access typeshed annotations.
- Tools that check stubs for correctness.
- Tools that use typeshed for runtime introspection.

Installation
------------

``typeshed_client`` works only on Python 3.6. To install it, run
``python3.6 -m pip install typeshed_client``.

Finding stubs
-------------

The `typeshed_client.finder` module provides functions for finding stub files
given a module name.

Functions provided:

- ``typeshed_client.get_stub_file(module_name: str,
  version: Tuple[int, int] = sys.version_info[:2],
  typeshed_dir: Optional[Path] = None) -> Optional[Path]``: Returns
  the path to a module's stub in typeshed. For example,
  ``get_stub_file('typing', version=(2, 7))`` may return
  ``Path('/path/to/typeshed/stdlib/2/typing.pyi')``. If there is no stub for the
  module, returns None.
- ``typeshed_client.get_stub_ast`` has the same interface, but returns an AST
  object (parsed using `typed_ast <https://www.github.com/python/typed_ast>`_).

Collecting names from stubs
---------------------------

``typeshed_client.parser`` collects the names defined in a stub. It provides:

- ``typeshed_client.get_stub_names(module_name: str,
  version: Tuple[int, int] = sys.version_info[:2],
  platform: str = sys.platform,
  typeshed_dir: Optional[Path] = None) -> Optional[NameDict]`` collects the names
  defined in a module, using the given Python version and platform. It
  returns a ``NameDict``, a dictionary mapping object names defined in the module
  to ``NameInfo`` records.
- ``typeshed_client.NameInfo`` is a namedtuple defined as:

  .. code-block:: python

      class NameInfo(NamedTuple):
        name: str
        is_exported: bool
        ast: Union[ast3.AST, ImportedName, OverloadedName]
        child_nodes: Optional['NameDict'] = None

  ``name`` is the object's name. ``is_exported`` indicates whether the name is a
  part of the stub's public interface. ``ast`` is the AST node defining the name,
  or a different structure if the name is imported from another module or is
  overloaded. For classes, ``child_nodes`` is a dictionary containing the names
  defined within the class.

Resolving names to their definitions
------------------------------------

The third component of this package, ``typeshed_client.resolver``, maps names to
their definitions, even if those names are defined in other stubs.

To use the resolver, you need to instantiate the ``typeshed_client.Resolver``
class. For example, given a ``resolver = typeshed_client.Resolver()``, you can
call ``resolver.get_fully_qualified_name('collections.Set')`` to retrieve the
``NameInfo`` containing the AST node defining ``collections.Set`` in typeshed.

Changelog
---------

Version 0.3 (November 23, 2019)

- Update location of typeshed for newer mypy versions

Version 0.2 (May 25, 2017)

- Support using a custom typeshed directory
- Add ``get_all_stub_files()``
- Handle ``from module import *``
- Bug fixes

Version 0.1 (May 4, 2017)

- Initial release

Future work
-----------

- Fall back to builtins correctly in the resolver.
- Maybe provide ways to map AST nodes in annotations to runtime type objects.
