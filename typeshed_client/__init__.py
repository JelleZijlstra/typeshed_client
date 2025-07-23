"""Package for retrieving data from typeshed."""

# Exported names
from .finder import (
    ModulePath,
    SearchContext,
    get_all_stub_files,
    get_search_context,
    get_stub_ast,
    get_stub_file,
)
from .parser import (
    ImportedName,
    NameDict,
    NameInfo,
    OverloadedName,
    get_stub_names,
    parse_ast,
)
from .resolver import ImportedInfo, Resolver

__version__ = "2.8.2"


__all__ = [
    "ImportedInfo",
    "ImportedName",
    "ModulePath",
    "NameDict",
    "NameInfo",
    "OverloadedName",
    "Resolver",
    "SearchContext",
    "__version__",
    "get_all_stub_files",
    "get_search_context",
    "get_stub_ast",
    "get_stub_file",
    "get_stub_names",
    "parse_ast",
]
