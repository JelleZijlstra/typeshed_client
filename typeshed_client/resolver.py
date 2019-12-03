"""Module responsible for resolving names to the module they come from."""

from pathlib import Path
import sys
from typing import Dict, NamedTuple, Optional, Tuple, Union

from . import finder
from . import parser


class ImportedInfo(NamedTuple):
    source_module: parser.ModulePath
    info: parser.NameInfo


ResolvedName = Union[None, parser.ModulePath, ImportedInfo, parser.NameInfo]


class Resolver:
    def __init__(
        self,
        version: Tuple[int, int] = sys.version_info[:2],
        platform: str = sys.platform,
        typeshed_dir: Optional[Path] = None,
    ) -> None:
        if typeshed_dir is None:
            typeshed_dir = finder.find_typeshed()
        self.env = parser.Env(version, platform, typeshed_dir)
        self._typeshed_dir = typeshed_dir
        self._module_cache: Dict[parser.ModulePath, Module] = {}

    def get_module(self, module_name: parser.ModulePath) -> "Module":
        if module_name not in self._module_cache:
            names = parser.get_stub_names(
                ".".join(module_name),
                version=self.env.version,
                platform=self.env.platform,
                typeshed_dir=self._typeshed_dir,
            )
            if names is None:
                names = {}
            self._module_cache[module_name] = Module(names, self.env)
        return self._module_cache[module_name]

    def get_name(self, module_name: parser.ModulePath, name: str) -> ResolvedName:
        module = self.get_module(module_name)
        return module.get_name(name, self)

    def get_fully_qualified_name(self, name: str) -> ResolvedName:
        """Public API."""
        *path, tail = name.split(".")
        return self.get_name(parser.ModulePath(tuple(path)), tail)


class Module:
    def __init__(self, names: parser.NameDict, env: parser.Env) -> None:
        self.names = names
        self.env = env
        self._name_cache: Dict[str, ResolvedName] = {}

    def get_name(self, name: str, resolver: Resolver) -> ResolvedName:
        if name not in self._name_cache:
            self._name_cache[name] = self._uncached_get_name(name, resolver)
        return self._name_cache[name]

    def _uncached_get_name(self, name: str, resolver: Resolver) -> ResolvedName:
        if name not in self.names:
            return None
        info = self.names[name]
        if not isinstance(info.ast, parser.ImportedName):
            return info
        # TODO prevent infinite recursion
        import_info = info.ast
        if import_info.name is not None:
            resolved = resolver.get_name(import_info.module_name, import_info.name)
            if isinstance(resolved, parser.NameInfo):
                return ImportedInfo(import_info.module_name, resolved)
            else:
                # TODO: preserve export information
                return resolved
        else:
            return import_info.module_name
