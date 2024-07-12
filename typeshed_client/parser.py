"""This module is responsible for parsing a stub AST into a dictionary of names."""

import ast
import logging
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    NoReturn,
    Optional,
    Tuple,
    Type,
    Union,
)

from . import finder
from .finder import ModulePath, SearchContext, get_search_context, parse_stub_file

log = logging.getLogger(__name__)


class InvalidStub(Exception):
    pass


class ImportedName(NamedTuple):
    module_name: ModulePath
    name: Optional[str] = None


class OverloadedName(NamedTuple):
    definitions: List[ast.AST]


class NameInfo(NamedTuple):
    name: str
    is_exported: bool
    ast: Union[ast.AST, ImportedName, OverloadedName]
    # should be Optional[NameDict] but that needs a recursive type
    child_nodes: Optional[Dict[str, Any]] = None


NameDict = Dict[str, NameInfo]


def get_stub_names(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[NameDict]:
    """Given a module name, return a dictionary of names defined in that module."""
    if search_context is None:
        search_context = get_search_context()
    path = finder.get_stub_file(module_name, search_context=search_context)
    if path is None:
        return None
    is_init = path.name == "__init__.pyi"
    ast = parse_stub_file(path)
    return parse_ast(
        ast, search_context, ModulePath(tuple(module_name.split("."))), is_init=is_init
    )


def parse_ast(
    ast: ast.AST,
    search_context: SearchContext,
    module_name: ModulePath,
    *,
    is_init: bool = False,
) -> NameDict:
    visitor = _NameExtractor(search_context, module_name, is_init=is_init)
    name_dict: NameDict = {}
    try:
        names = visitor.visit(ast)
    except _AssertFailed:
        return name_dict
    for info in names:
        if info.name in name_dict:
            if info.child_nodes:
                _warn(
                    f"Name is already present in {', '.join(module_name)}: {info}",
                    search_context,
                )
                continue
            existing = name_dict[info.name]

            # This is common and harmless, likely from an "import *"
            if isinstance(existing.ast, ImportedName) and isinstance(
                info.ast, ImportedName
            ):
                continue

            if isinstance(existing.ast, ImportedName):
                _warn(
                    f"Name is already imported in {', '.join(module_name)}: {existing}",
                    search_context,
                )
            elif existing.child_nodes:
                _warn(
                    f"Name is already present in {', '.join(module_name)}: {existing}",
                    search_context,
                )
            elif isinstance(existing.ast, OverloadedName):
                existing.ast.definitions.append(info.ast)
            else:
                new_info = NameInfo(
                    existing.name,
                    existing.is_exported,
                    OverloadedName([existing.ast, info.ast]),
                )
                name_dict[info.name] = new_info
        else:
            name_dict[info.name] = info
    return name_dict


def get_import_star_names(
    module_name: str, *, search_context: SearchContext
) -> Optional[List[str]]:
    name_dict = get_stub_names(module_name, search_context=search_context)
    if name_dict is None:
        return None
    if "__all__" in name_dict:
        info = name_dict["__all__"]
        return get_dunder_all_from_info(info)
    return [name for name, info in name_dict.items() if info.is_exported]


def get_dunder_all_from_info(info: NameInfo) -> Optional[List[str]]:
    if isinstance(info.ast, OverloadedName):
        names = []
        for defn in info.ast.definitions:
            subnames = _get_dunder_all_from_ast(defn)
            if subnames is None:
                raise InvalidStub(f"Invalid __all__: {info}")
            names += subnames
        return names
    if isinstance(info.ast, ImportedName):
        raise InvalidStub(f"Invalid __all__: {info}")
    return _get_dunder_all_from_ast(info.ast)


def _get_dunder_all_from_ast(node: ast.AST) -> Optional[List[str]]:
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


_CMP_OP_TO_FUNCTION: Dict[Type[ast.AST], Callable[[Any, Any], bool]] = {
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
        self, ctx: SearchContext, module_name: ModulePath, *, is_init: bool = False
    ) -> None:
        self.ctx = ctx
        self.module_name = module_name
        self.is_init = is_init

    def visit_Module(self, node: ast.Module) -> List[NameInfo]:
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
                raise InvalidStub(
                    f"Assignment should only be to a simple name: {ast.dump(node)}"
                )
            yield NameInfo(target.id, _name_is_exported(target.id), node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Iterable[NameInfo]:
        if not isinstance(node.op, ast.Add):
            raise InvalidStub(f"Only += is allowed in stubs: {ast.dump(node)}")
        if not isinstance(node.target, ast.Name) or node.target.id != "__all__":
            raise InvalidStub(f"+= is allowed only for __all__: {ast.dump(node)}")
        yield NameInfo("__all__", True, node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Iterable[NameInfo]:
        target = node.target
        if not isinstance(target, ast.Name):
            raise InvalidStub(
                f"Assignment should only be to a simple name: {ast.dump(node)}"
            )
        yield NameInfo(target.id, _name_is_exported(target.id), node)

    def visit_If(self, node: ast.If) -> Iterable[NameInfo]:
        visitor = _LiteralEvalVisitor(self.ctx)
        value = visitor.visit(node.test)
        if value:
            for stmt in node.body:
                yield from self.visit(stmt)
        else:
            for stmt in node.orelse:
                yield from self.visit(stmt)

    def visit_Try(self, node: ast.Try) -> Iterable[NameInfo]:
        # try-except sometimes gets used with conditional imports. We assume
        # the try block is always executed.
        for stmt in node.body:
            yield from self.visit(stmt)
        for stmt in node.finalbody:
            yield from self.visit(stmt)

    def visit_Assert(self, node: ast.Assert) -> Iterable[NameInfo]:
        visitor = _LiteralEvalVisitor(self.ctx)
        value = visitor.visit(node.test)
        if value:
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
        module: Tuple[str, ...]
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
                    ".".join(source_module), search_context=self.ctx
                )
                if names is None:
                    _warn(
                        f"could not import {source_module} in"
                        f" {self.module_name} with {self.ctx}",
                        self.ctx,
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
            raise InvalidStub(f"Cannot handle node {ast.dump(node)}")

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

    def generic_visit(self, node: ast.AST) -> NoReturn:
        raise InvalidStub(f"Cannot handle node {ast.dump(node)}")


class _LiteralEvalVisitor(ast.NodeVisitor):
    def __init__(self, ctx: SearchContext) -> None:
        self.ctx = ctx

    def visit_Constant(self, node: ast.Constant) -> object:
        return node.value

    # from version 3.9 on an index is represented as the value directly
    if sys.version_info < (3, 9):

        def visit_Index(self, node: ast.Index) -> int:
            return self.visit(node.value)

    def visit_Tuple(self, node: ast.Tuple) -> Tuple[object, ...]:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_Subscript(self, node: ast.Subscript) -> object:
        value = self.visit(node.value)
        slc = self.visit(node.slice)
        return value[slc]

    def visit_Compare(self, node: ast.Compare) -> bool:
        if len(node.ops) != 1:
            raise InvalidStub(f"Cannot evaluate chained comparison {ast.dump(node)}")
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
            raise InvalidStub(f"Invalid code in stub: {ast.dump(node)}")
        if val.id != "sys":
            raise InvalidStub(
                f"Attribute access must be on the sys module: {ast.dump(node)}"
            )
        if node.attr == "platform":
            return self.ctx.platform
        elif node.attr == "version_info":
            return self.ctx.version
        else:
            raise InvalidStub(f"Invalid attribute on {ast.dump(node)}")

    def visit_Name(self, node: ast.Name) -> bool:
        # We're type checking (probably), but we're not mypy.
        if node.id == "TYPE_CHECKING":
            return True
        elif node.id == "MYPY":
            return False
        else:
            raise InvalidStub(f"Invalid name {node.id!r} in stub condition")

    def generic_visit(self, node: ast.AST) -> NoReturn:
        raise InvalidStub(f"Cannot evaluate node {ast.dump(node)}")


class _AssertFailed(Exception):
    """Raised when a top-level assert in a stub fails."""


def _warn(message: str, ctx: SearchContext) -> None:
    if ctx.raise_on_warnings:
        raise InvalidStub(message)
    else:
        log.warning(message)
