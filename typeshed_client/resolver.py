"""Module responsible for resolving names to the module they come from."""

from typing import NamedTuple, Optional, Union

from . import parser
from .finder import ModulePath, SearchContext, get_search_context


class ImportedInfo(NamedTuple):
    source_module: ModulePath
    info: parser.NameInfo


ResolvedName = Union[ModulePath, ImportedInfo, parser.NameInfo, None]


class Resolver:
    def __init__(self, search_context: Optional[SearchContext] = None) -> None:
        if search_context is None:
            search_context = get_search_context()
        self.ctx = search_context
        self._module_cache: dict[ModulePath, Module] = {}

    def get_module(self, module_name: ModulePath) -> "Module":
        if module_name not in self._module_cache:
            names = parser.get_stub_names(
                ".".join(module_name), search_context=self.ctx
            )
            exists = names is not None
            if names is None:
                names = {}
            self._module_cache[module_name] = Module(names, self.ctx, exists=exists)
        return self._module_cache[module_name]

    def get_name(self, module_name: ModulePath, name: str) -> ResolvedName:
        module = self.get_module(module_name)
        return module.get_name(name, self)

    def get_fully_qualified_name(self, name: str) -> ResolvedName:
        """Public API."""
        *path, tail = name.split(".")
        return self.get_name(ModulePath(tuple(path)), tail)


class Module:
    def __init__(
        self, names: parser.NameDict, ctx: SearchContext, *, exists: bool = True
    ) -> None:
        self.names = names
        self.ctx = ctx
        self._name_cache: dict[str, ResolvedName] = {}
        self.exists = exists

    def get_name(self, name: str, resolver: Resolver) -> ResolvedName:
        if name not in self._name_cache:
            self._name_cache[name] = self._uncached_get_name(name, resolver)
        return self._name_cache[name]

    def get_dunder_all(self, resolver: Resolver) -> Optional[list[str]]:
        """Return the contents of __all__, or None if it does not exist."""
        resolved_name = self.get_name("__all__", resolver)
        if resolved_name is None:
            return None
        if isinstance(resolved_name, ImportedInfo):
            resolved_name = resolved_name.info
        if not isinstance(resolved_name, parser.NameInfo):
            raise parser.InvalidStub(f"Invalid __all__: {resolved_name}")
        return parser.get_dunder_all_from_info(resolved_name)

    def _uncached_get_name(self, name: str, resolver: Resolver) -> ResolvedName:
        if name not in self.names:
            return None
        info = self.names[name]
        if not isinstance(info.ast, parser.ImportedName):
            return info
        # TODO prevent infinite recursion
        import_info = info.ast
        if import_info.name is not None:
            module_path = ModulePath((*import_info.module_name, import_info.name))
            module = resolver.get_module(module_path)
            if module.exists:
                return module_path
            resolved = resolver.get_name(import_info.module_name, import_info.name)
            if isinstance(resolved, parser.NameInfo):
                return ImportedInfo(import_info.module_name, resolved)
            else:
                # TODO: preserve export information
                return resolved
        else:
            return import_info.module_name
