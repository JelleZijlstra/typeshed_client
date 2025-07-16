"""This module is responsible for parsing a stub AST into a dictionary of names."""

import ast
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, NamedTuple, NoReturn, Optional, Union

from . import finder
from .finder import ModulePath, SearchContext, get_search_context, parse_stub_file

log = logging.getLogger(__name__)


class InvalidStub(Exception):
    def __init__(self, message: str, file_path: Optional[Path] = None) -> None:
        if file_path is not None:
            message = f"{file_path}: {message}"
        super().__init__(message)


class ImportedName(NamedTuple):
    module_name: ModulePath
    name: Optional[str] = None


class OverloadedName(NamedTuple):
    definitions: list[Union[ast.AST, ImportedName]]


class NameInfo(NamedTuple):
    name: str
    is_exported: bool
    ast: Union[ast.AST, ImportedName, OverloadedName]
    # should be Optional[NameDict] but that needs a recursive type
    child_nodes: Optional[dict[str, Any]] = None


NameDict = dict[str, NameInfo]


def get_stub_names(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[NameDict]:
    """Given a module name, return a dictionary of names defined in that module."""
    if search_context is None:
        search_context = get_search_context()
    path = finder.get_stub_file(module_name, search_context=search_context)
    if path is None:
        return None
    is_init = path.name in ("__init__.py", "__init__.pyi")
    ast = parse_stub_file(path)
    return parse_ast(
        ast,
        search_context,
        ModulePath(tuple(module_name.split("."))),
        is_init=is_init,
        file_path=path,
        is_py_file=path.suffix == ".py",
    )


def parse_ast(
    ast: ast.AST,
    search_context: SearchContext,
    module_name: ModulePath,
    *,
    is_init: bool = False,
    file_path: Optional[Path] = None,
    is_py_file: bool = False,
) -> NameDict:
    visitor = _NameExtractor(
        search_context,
        module_name,
        is_init=is_init,
        file_path=file_path,
        is_py_file=is_py_file,
    )
    name_dict: NameDict = {}
    try:
        names: Iterable[NameInfo] = visitor.visit(ast)
    except _AssertFailed:
        return name_dict
    for info in names:
        if info.name in name_dict:
            existing = name_dict[info.name]
            if isinstance(existing.ast, ImportedName):
                # If it's imported, allow to just overwrite it
                name_dict[info.name] = info
                continue

            if info.child_nodes:
                _warn(
                    f"Name is already present in {', '.join(module_name)}: {info}",
                    search_context,
                    file_path,
                )
                continue

            # This is common and harmless, likely from an "import *"
            if existing == info:
                continue
            elif existing.child_nodes:
                _warn(
                    f"Name is already present in {', '.join(module_name)}: {info}",
                    search_context,
                    file_path,
                )
            elif isinstance(info.ast, OverloadedName):
                # Should not happen
                _warn(
                    f"Name is already present in {', '.join(module_name)}: {info}",
                    search_context,
                    file_path,
                )
            elif isinstance(existing.ast, OverloadedName):
                if info.is_exported and not existing.is_exported:
                    new_info = NameInfo(
                        existing.name,
                        True,
                        OverloadedName([*existing.ast.definitions, info.ast]),
                    )
                    name_dict[info.name] = new_info
                else:
                    existing.ast.definitions.append(info.ast)
            else:
                new_info = NameInfo(
                    existing.name,
                    existing.is_exported or info.is_exported,
                    OverloadedName([existing.ast, info.ast]),
                )
                name_dict[info.name] = new_info
        else:
            name_dict[info.name] = info
    return name_dict


def get_import_star_names(
    module_name: str, *, search_context: SearchContext, file_path: Optional[Path] = None
) -> Optional[list[str]]:
    name_dict = get_stub_names(module_name, search_context=search_context)
    if name_dict is None:
        return None
    if "__all__" in name_dict:
        info = name_dict["__all__"]
        return get_dunder_all_from_info(info, file_path)
    return [name for name, info in name_dict.items() if info.is_exported]


def get_dunder_all_from_info(
    info: NameInfo, file_path: Optional[Path] = None
) -> Optional[list[str]]:
    if isinstance(info.ast, OverloadedName):
        names = []
        for defn in info.ast.definitions:
            if isinstance(defn, ImportedName):
                raise InvalidStub(f"Invalid __all__: {info}", file_path)
            subnames = _get_dunder_all_from_ast(defn)
            if subnames is None:
                raise InvalidStub(f"Invalid __all__: {info}", file_path)
            names += subnames
        return names
    if isinstance(info.ast, ImportedName):
        raise InvalidStub(f"Invalid __all__: {info}", file_path)
    return _get_dunder_all_from_ast(info.ast)


def _get_dunder_all_from_ast(node: ast.AST) -> Optional[list[str]]:
    if isinstance(node, (ast.Assign, ast.AugAssign)):
        rhs = node.value
    elif isinstance(node, (ast.List, ast.Tuple)):
        rhs = node
    else:
        raise InvalidStub(f"Invalid __all__: {ast.dump(node)}")
    if not isinstance(rhs, (ast.List, ast.Tuple)):
        raise InvalidStub(f"Invalid __all__: {ast.dump(rhs)}")
    names = []
    for elt in rhs.elts:
        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
            raise InvalidStub(f"Invalid __all__: {ast.dump(rhs)}")
        names.append(elt.value)
    return names


_CMP_OP_TO_FUNCTION: dict[type[ast.AST], Callable[[Any, Any], bool]] = {
    ast.Eq: lambda x, y: x == y,
    ast.NotEq: lambda x, y: x != y,
    ast.Lt: lambda x, y: x < y,
    ast.LtE: lambda x, y: x <= y,
    ast.Gt: lambda x, y: x > y,
    ast.GtE: lambda x, y: x >= y,
    ast.Is: lambda x, y: x is y,
    ast.IsNot: lambda x, y: x is not y,
    ast.In: lambda x, y: x in y,
    ast.NotIn: lambda x, y: x not in y,
}


def _name_is_exported(name: str) -> bool:
    return not name.startswith("_")


class _NameExtractor(ast.NodeVisitor):
    """Extract names from a stub module."""

    def __init__(
        self,
        ctx: SearchContext,
        module_name: ModulePath,
        *,
        is_init: bool = False,
        file_path: Optional[Path],
        is_py_file: bool = False,
    ) -> None:
        self.ctx = ctx
        self.module_name = module_name
        self.is_init = is_init
        self.file_path = file_path
        self.is_py_file = is_py_file

    def visit_Module(self, node: ast.Module) -> list[NameInfo]:
        return [info for child in node.body for info in self.visit(child)]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Iterable[NameInfo]:
        yield NameInfo(node.name, _name_is_exported(node.name), node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Iterable[NameInfo]:
        yield NameInfo(node.name, _name_is_exported(node.name), node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Iterable[NameInfo]:
        children = [info for child in node.body for info in self.visit(child)]
        child_dict: NameDict = {}
        for info in children:
            if info.name in child_dict:
                existing = child_dict[info.name]
                if isinstance(existing.ast, OverloadedName):
                    existing.ast.definitions.append(info.ast)
                elif isinstance(existing.ast, ImportedName):
                    if self.is_py_file:
                        continue
                    raise RuntimeError(
                        f"Unexpected import name in class: {existing.ast}"
                    )
                else:
                    new_info = NameInfo(
                        existing.name,
                        existing.is_exported,
                        OverloadedName([existing.ast, info.ast]),
                    )
                    child_dict[info.name] = new_info
            else:
                child_dict[info.name] = info
        yield NameInfo(node.name, _name_is_exported(node.name), node, child_dict)

    def visit_Assign(self, node: ast.Assign) -> Iterable[NameInfo]:
        for target in node.targets:
            if not isinstance(target, ast.Name):
                if self.is_py_file:
                    continue
                raise InvalidStub(
                    f"Assignment should only be to a simple name: {ast.dump(node)}",
                    self.file_path,
                )
            yield NameInfo(target.id, _name_is_exported(target.id), node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Iterable[NameInfo]:
        if not isinstance(node.op, ast.Add):
            if self.is_py_file:
                return
            raise InvalidStub(
                f"Only += is allowed in stubs: {ast.dump(node)}", self.file_path
            )
        if not isinstance(node.target, ast.Name) or node.target.id != "__all__":
            if self.is_py_file:
                return
            raise InvalidStub(
                f"+= is allowed only for __all__: {ast.dump(node)}", self.file_path
            )
        yield NameInfo("__all__", True, node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Iterable[NameInfo]:
        target = node.target
        if not isinstance(target, ast.Name):
            if self.is_py_file:
                return
            raise InvalidStub(
                f"Assignment should only be to a simple name: {ast.dump(node)}",
                self.file_path,
            )
        yield NameInfo(target.id, _name_is_exported(target.id), node)

    def visit_If(self, node: ast.If) -> Iterable[NameInfo]:
        value = self._visit_condition(node.test)
        if value is None:
            # We don't know which branch to take, so we assume both
            for stmt in node.body:
                yield from self.visit(stmt)
            for stmt in node.orelse:
                yield from self.visit(stmt)
        elif value:
            for stmt in node.body:
                yield from self.visit(stmt)
        else:
            for stmt in node.orelse:
                yield from self.visit(stmt)

    def _visit_condition(self, expr: ast.expr) -> Optional[bool]:
        visitor = _LiteralEvalVisitor(self.ctx, self.file_path)
        try:
            value = visitor.visit(expr)
        except InvalidStub:
            if not self.is_py_file:
                raise
            return None
        else:
            return bool(value)

    def visit_Try(self, node: ast.Try) -> Iterable[NameInfo]:
        # try-except sometimes gets used with conditional imports. We assume
        # the try block is always executed.
        for stmt in node.body:
            yield from self.visit(stmt)
        for stmt in node.finalbody:
            yield from self.visit(stmt)

    def visit_Assert(self, node: ast.Assert) -> Iterable[NameInfo]:
        value = self._visit_condition(node.test)
        if value is True or value is None:
            return []
        else:
            raise _AssertFailed

    def visit_Import(self, node: ast.Import) -> Iterable[NameInfo]:
        for alias in node.names:
            if alias.asname is not None:
                yield NameInfo(
                    alias.asname,
                    True,
                    ImportedName(ModulePath(tuple(alias.name.split(".")))),
                )
            else:
                # "import a.b" just binds the name "a"
                name = alias.name.split(".", 1)[0]
                yield NameInfo(name, False, ImportedName(ModulePath((name,))))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Iterable[NameInfo]:
        module: tuple[str, ...]
        module = () if node.module is None else tuple(node.module.split("."))
        if node.level == 0:
            source_module = ModulePath(module)
        elif node.level == 1:
            if self.is_init:
                source_module = ModulePath(self.module_name + module)
            else:
                source_module = ModulePath(self.module_name[:-1] + module)
        else:
            if self.is_init:
                source_module = ModulePath(self.module_name[: 1 - node.level] + module)
            else:
                source_module = ModulePath(self.module_name[: -node.level] + module)
        for alias in node.names:
            if alias.asname is not None:
                is_exported = _name_is_exported(alias.asname)
                yield NameInfo(
                    alias.asname, is_exported, ImportedName(source_module, alias.name)
                )
            elif alias.name == "*":
                names = get_import_star_names(
                    ".".join(source_module),
                    search_context=self.ctx,
                    file_path=self.file_path,
                )
                if names is None:
                    _warn(
                        f"could not import {source_module} in"
                        f" {self.module_name} with {self.ctx}",
                        self.ctx,
                        self.file_path,
                    )
                    continue
                for name in names:
                    yield NameInfo(name, True, ImportedName(source_module, name))
            else:
                yield NameInfo(
                    alias.name, False, ImportedName(source_module, alias.name)
                )

    def visit_Expr(self, node: ast.Expr) -> Iterable[NameInfo]:
        if isinstance(node.value, ast.Constant) and (
            node.value.value is Ellipsis or isinstance(node.value.value, str)
        ):
            return
        dunder_all = self._maybe_extract_dunder_all(node.value)
        if dunder_all is not None:
            yield dunder_all
        else:
            if self.is_py_file:
                # We don't know what this is, so we ignore it
                return
            raise InvalidStub(f"Cannot handle node {ast.dump(node)}", self.file_path)

    def _maybe_extract_dunder_all(self, node: ast.expr) -> Optional[NameInfo]:
        if not isinstance(node, ast.Call):
            return None
        if not isinstance(node.func, ast.Attribute):
            return None
        if not isinstance(node.func.value, ast.Name):
            return None
        if node.func.value.id != "__all__":
            return None
        if len(node.args) != 1 or node.keywords:
            return None
        arg = node.args[0]
        if isinstance(arg, ast.Starred):
            return None
        if node.func.attr == "extend":
            return NameInfo("__all__", True, arg)
        elif node.func.attr == "append":
            return NameInfo("__all__", True, ast.List(elts=[arg], ctx=ast.Load()))
        else:
            return None

    def visit_Pass(self, node: ast.Pass) -> Iterable[NameInfo]:
        return []

    def generic_visit(self, node: ast.AST) -> Iterable[NameInfo]:
        if self.is_py_file:
            # We don't know what this is, so we ignore it
            return []
        raise InvalidStub(f"Cannot handle node {ast.dump(node)}", self.file_path)


class _LiteralEvalVisitor(ast.NodeVisitor):
    def __init__(self, ctx: SearchContext, file_path: Optional[Path]) -> None:
        self.ctx = ctx
        self.file_path = file_path

    def visit_Constant(self, node: ast.Constant) -> object:
        return node.value

    def visit_Tuple(self, node: ast.Tuple) -> tuple[object, ...]:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_Subscript(self, node: ast.Subscript) -> object:
        value = self.visit(node.value)
        slc = self.visit(node.slice)
        return value[slc]

    def visit_Compare(self, node: ast.Compare) -> bool:
        if len(node.ops) != 1:
            raise InvalidStub(
                f"Cannot evaluate chained comparison {ast.dump(node)}", self.file_path
            )
        fn = _CMP_OP_TO_FUNCTION[type(node.ops[0])]
        return fn(self.visit(node.left), self.visit(node.comparators[0]))

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        for val_node in node.values:
            val = self.visit(val_node)
            if (isinstance(node.op, ast.Or) and val) or (
                isinstance(node.op, ast.And) and not val
            ):
                return val
        return val

    def visit_Slice(self, node: ast.Slice) -> slice:
        lower = self.visit(node.lower) if node.lower is not None else None
        upper = self.visit(node.upper) if node.upper is not None else None
        step = self.visit(node.step) if node.step is not None else None
        return slice(lower, upper, step)

    def visit_Attribute(self, node: ast.Attribute) -> object:
        val = node.value
        if not isinstance(val, ast.Name):
            raise InvalidStub(f"Invalid code in stub: {ast.dump(node)}", self.file_path)
        if val.id != "sys":
            raise InvalidStub(
                f"Attribute access must be on the sys module: {ast.dump(node)}",
                self.file_path,
            )
        if node.attr == "platform":
            return self.ctx.platform
        elif node.attr == "version_info":
            return self.ctx.version
        else:
            raise InvalidStub(f"Invalid attribute on {ast.dump(node)}", self.file_path)

    def visit_Name(self, node: ast.Name) -> bool:
        # We're type checking (probably), but we're not mypy.
        if node.id == "TYPE_CHECKING":
            return True
        elif node.id == "MYPY":
            return False
        else:
            raise InvalidStub(
                f"Invalid name {node.id!r} in stub condition", self.file_path
            )

    def generic_visit(self, node: ast.AST) -> NoReturn:
        raise InvalidStub(f"Cannot evaluate node {ast.dump(node)}")


class _AssertFailed(Exception):
    """Raised when a top-level assert in a stub fails."""


def _warn(message: str, ctx: SearchContext, file_path: Optional[Path]) -> None:
    if ctx.raise_on_warnings:
        raise InvalidStub(message, file_path)
    else:
        if file_path is not None:
            message = f"{file_path}: {message}"
        log.warning(message)
