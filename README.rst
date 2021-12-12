This project provides a way to retrieve information from
`typeshed <https://www.github.com/python/typeshed>`_ and from
`PEP 561 <https://www.python.org/dev/peps/pep-0561/>`_ stub packages.

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

``typeshed_client`` works on Python 3.6 and higher. To install it, run
``python3 -m pip install typeshed_client``.

Finding stubs
-------------

The `typeshed_client.finder` module provides functions for finding stub files
given a module name.

Functions provided:

- ``get_search_context(*, typeshed: Optional[Path] = None,
  search_path: Optional[Sequence[Path]] = None, python_executable: Optional[str] = None,
  version: Optional[PythonVersion] = None, platform: str = sys.platform) -> SearchContext``:
  Returns a ``SearchContext``
- ``typeshed_client.get_stub_file(module_name: str, *,
  search_context: Optional[SearchContext] = None) -> Optional[Path]``: Returns
  the path to a module's stub in typeshed. For example,
  ``get_stub_file('typing', search_context=get_search_context(version=(2, 7)))`` may return
  ``Path('/path/to/typeshed/stdlib/@python2/typing.pyi')``. If there is no stub for the
  module, returns None.
- ``typeshed_client.get_stub_ast`` has the same interface, but returns an AST
  object (parsed using `typed_ast <https://www.github.com/python/typed_ast>`_).

Collecting names from stubs
---------------------------

``typeshed_client.parser`` collects the names defined in a stub. It provides:

- ``typeshed_client.get_stub_names(module_name: str, *,
  search_context: Optional[SearchContext] = None) -> Optional[NameDict]`` collects the names
  defined in a module, using the given Python version and platform. It
  returns a ``NameDict``, a dictionary mapping object names defined in the module
  to ``NameInfo`` records.
- ``typeshed_client.NameInfo`` is a namedtuple defined as:

  .. code-block:: python

      class NameInfo(NamedTuple):
        name: str
        is_exported: bool
        ast: Union[ast3.AST, ImportedName, OverloadedName]
        child_nodes: Optional[NameDict] = None

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

Version 1.2.3 (December 12, 2021)

- Update bundled typeshed
- Remove noisy warning if a name is imported multiple times
- Fix `get_all_stub_files()` in Python 3 for modules that also exist in Python 2

Version 1.2.2 (December 9, 2021)

- Further fix relative import resolution

Version 1.2.1 (December 9, 2021)

- Fix bug with resolution of relative imports
- Update bundled typeshed

Version 1.2.0 (December 6, 2021)

- Support overloaded methods
- Update bundled typeshed

Version 1.1.4 (December 6, 2021)

- Updated bundled typeshed

Version 1.1.3 (November 14, 2021)

- Update bundled typeshed
- Declare support for Python 3.10
- Fix undeclared dependency on ``mypy_extensions``

Version 1.1.2 (November 5, 2021)

- Update bundled typeshed

Version 1.1.1 (July 31, 2021)

- Update bundled typeshed
- Improve error message when encountering a duplicate name

Version 1.1.0 (June 24, 2021)

- Update bundled typeshed
- Handle missing `@python2` directory
- Allow comments in VERSIONS file

Version 1.0.2 (May 5, 2021)

- Handle version ranges in typeshed VERSIONS file
- Update bundled typeshed

Version 1.0.1 (April 24, 2021)

- Update bundled typeshed

Version 1.0.0 (April 11, 2021)

- Improve docstrings

Version 1.0.0rc1 (April 11, 2021)

- Support new typeshed layout
- Support PEP 561 packages
- Bundle typeshed directly instead of relying on mypy

Version 0.4 (December 2, 2019)

- Performance improvement
- Code quality improvements

Version 0.3 (November 23, 2019)

- Update location of typeshed for newer mypy versions

Version 0.2 (May 25, 2017)

- Support using a custom typeshed directory
- Add ``get_all_stub_files()``
- Handle ``from module import *``
- Bug fixes

Version 0.1 (May 4, 2017)

- Initial release
