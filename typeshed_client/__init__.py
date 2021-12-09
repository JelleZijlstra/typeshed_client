"""Package for retrieving data from typeshed."""
from . import finder
from . import parser
from . import resolver

# Exported names
from .finder import (
    get_stub_ast,
    get_stub_file,
    get_all_stub_files,
    get_search_context,
    SearchContext,
    ModulePath,
)
from .parser import (
    get_stub_names,
    parse_ast,
    ImportedName,
    NameDict,
    NameInfo,
    OverloadedName,
)
from .resolver import ImportedInfo, Resolver


__version__ = "1.2.1"
