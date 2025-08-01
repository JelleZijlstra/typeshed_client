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

``typeshed_client`` works on all supported versions of Python. To install it, run
``python3 -m pip install typeshed_client``.

Finding stubs
-------------

The `typeshed_client.finder` module provides functions for finding stub files
given a module name.

Functions provided:

- ``get_search_context(*, typeshed: Path | None = None,
  search_path: Sequence[Path] | None = None, python_executable: str | None = None,
  version: PythonVersion | None = None, platform: str = sys.platform,
  raise_on_warnings: bool = False, allow_py_files: bool = False) -> SearchContext``:
  Returns a ``SearchContext``, which can be used with most other functions to customize
  stub finding behavior. All arguments are optional and the rest of the package will use
  a ``SearchContext`` created with the default values if no explicit context is provided.
  The arguments are:

  - ``typeshed``: The path to the typeshed directory. If not provided, the package will
    use the bundled version of typeshed.
  - ``search_path``: A list of directories to search for stubs. If not provided,
    ``sys.path`` will be used.
  - ``python_executable``: The path to the Python executable to be used for determining
    ``search_path``.
  - ``version``: Version of Python (as a pair, e.g., ``(3, 13)``) to be used for
    interpreting ``sys.version_info`` checks in stubs.
  - ``platform``: The platform to be used for interpreting ``sys.platform`` checks in
    stubs. The default is ``sys.platform``, the platform where the library is invoked.
  - ``raise_on_warnings``: If True, raise an exception if the parser encounters something
    it does not understand.
  - ``allow_py_files``: If True, allow searching for ``.py`` files in addition to
    ``.pyi`` files. This is useful for typed packages that contain both stub files and
    regular Python files. The default is False.

- ``typeshed_client.get_stub_file(module_name: str, *,
  search_context: SearchContext | None = None) -> Path | None``: Returns
  the path to a module's stub file. For example,
  ``get_stub_file('typing')`` may return
  ``Path('/path/to/typeshed/stdlib/typing.pyi')``. If there is no stub for the
  module, returns None.
- ``typeshed_client.get_stub_ast`` has the same interface, but returns an AST
  object (parsed using the standard library ``ast`` module).

Collecting names from stubs
---------------------------

``typeshed_client.parser`` collects the names defined in a stub. It provides:

- ``typeshed_client.get_stub_names(module_name: str, *,
  search_context: SearchContext | None = None) -> NameDict | None`` collects the names
  defined in a module, using the given Python version and platform. It
  returns a ``NameDict``, a dictionary mapping object names defined in the module
  to ``NameInfo`` records.
- ``typeshed_client.NameInfo`` is a namedtuple defined as:

  .. code-block:: python

      class NameInfo(NamedTuple):
        name: str
        is_exported: bool
        ast: ast.AST | ImportedName | OverloadedName
        child_nodes: NameDict | None = None

  ``name`` is the object's name. ``is_exported`` indicates whether the name is a
  part of the stub's public interface. ``ast`` is the AST node defining the name,
  or a different structure if the name is imported from another module or is
  overloaded. For classes, ``child_nodes`` is a dictionary containing the names
  defined within the class.

Resolving names to their definitions
------------------------------------

The third component of this package, ``typeshed_client.resolver``, maps names to
their definitions, even if those names are defined in other stubs.

To use the resolver, instantiate the ``typeshed_client.Resolver``
class. For example, given a ``resolver = typeshed_client.Resolver()``, you can
call ``resolver.get_fully_qualified_name('collections.Set')`` to retrieve the
``NameInfo`` containing the AST node defining ``collections.Set`` in typeshed.

Changelog
---------

Version 2.8.1 (July 15, 2025)

- Fix package publishing pipeline

Version 2.8.0 (July 15, 2025)

- Update bundled typeshed
- Drop support for Python 3.8 and add preliminary support for Python 3.14
- Search for names and imports in ``.py`` files in addition to ``.pyi`` files
- Allow more redefinitions in stub files. ``OverloadedName`` objects can now
  contain ``ImportedName`` objects.
- Explicitly set encoding to UTF-8, fixing crashes on Windows in some cases.

Version 2.7.0 (July 16, 2024)

- Update bundled typeshed

Version 2.6.0 (July 12, 2024)

- Update bundled typeshed
- Support ``try`` blocks in stubs
- Declare support for Python 3.13
- Handle situations where an entry on the module search path is not
  accessible or does not exist
- Fix warnings due to use of deprecated AST classes

Version 2.5.1 (February 25, 2024)

- Fix packaging metadata that still incorrectly declared support for Python 3.7

Version 2.5.0 (February 25, 2024)

- Update bundled typeshed
- Drop support for Python 3.7
- ``typeshed_client.finder.get_search_path()`` is now deprecated, as it is no longer useful

Version 2.4.0 (September 29, 2023)

- Update bundled typeshed
- Declare support for Python 3.12

Version 2.3.0 (April 30, 2023)

- Update bundled typeshed
- Support ``__all__.append`` and ``__all__.extend``

Version 2.2.0 (January 24, 2023)

- Update bundled typeshed
- Fix crash on stubs that use ``if MYPY``
- Fix incorrect handling of ``import *`` in stubs
- Drop support for Python 3.6 (thanks to Alex Waygood)

Version 2.1.0 (November 5, 2022)

- Update bundled typeshed
- Declare support for Python 3.11
- Add ``typeshed_client.resolver.Module.get_dunder_all`` to get the contents of ``__all__``
- Add support for ``__all__ +=`` syntax
- Type check the code using mypy (thanks to Nicolas)

Version 2.0.5 (April 17, 2022)

- Update bundled typeshed

Version 2.0.4 (March 10, 2022)

- Update bundled typeshed

Version 2.0.3 (February 2, 2022)

- Update bundled typeshed

Version 2.0.2 (January 28, 2022)

- Update bundled typeshed

Version 2.0.1 (January 14, 2022)

- Update bundled typeshed

Version 2.0.0 (December 22, 2021)

- Breaking change: Use `ast` instead of `typed_ast` for parsing

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
