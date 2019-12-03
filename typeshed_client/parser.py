"""This module is responsible for parsing a stub AST into a dictionary of names."""

import logging
from mypy_extensions import NoReturn
from pathlib import Path
import sys
from typed_ast import ast3
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    NewType,
    Optional,
    Tuple,
    Union,
)

from . import finder

log = logging.getLogger(__name__)


class InvalidStub(Exception):
    pass


ModulePath = NewType("ModulePath", Tuple[str, ...])


class ImportedName(NamedTuple):
    module_name: ModulePath
    name: Optional[str] = None


class OverloadedName(NamedTuple):
    definitions: List[ast3.AST]


class NameInfo(NamedTuple):
    name: str
    is_exported: bool
    ast: Union[ast3.AST, ImportedName, OverloadedName]
    # should be Optional[NameDict] but that needs a recursive type
    child_nodes: Optional[Dict[str, Any]] = None


class Env(NamedTuple):
    version: Tuple[int, int]
    platform: str
    typeshed_dir: Path


NameDict = Dict[str, NameInfo]


def get_stub_names(
    module_name: str,
    version: Tuple[int, int] = sys.version_info[:2],
    platform: str = sys.platform,
    typeshed_dir: Optional[Path] = None,
) -> Optional[NameDict]:
    """Given a module name, returns a dictionary of names defined in that module."""
    if typeshed_dir is None:
        typeshed_dir = finder.find_typeshed()
    ast = finder.get_stub_ast(module_name, version=version, typeshed_dir=typeshed_dir)
    if ast is None:
        return None
    return parse_ast(
        ast,
        Env(version, platform, typeshed_dir),
        ModulePath(tuple(module_name.split("."))),
    )


def parse_ast(ast: ast3.AST, env: Env, module_name: ModulePath) -> NameDict:
    visitor = _NameExtractor(env, module_name)
    names = visitor.visit(ast)
    name_dict: NameDict = {}
    for info in names:
        if info.name in name_dict:
            if isinstance(info.ast, ImportedName) or info.child_nodes:
                log.warning("Cannot overload a class or an imported name: %s", info)
                continue
            existing = name_dict[info.name]
            if isinstance(existing.ast, ImportedName) or existing.child_nodes:
                log.warning("Cannot overload a class or an imported name: %s", existing)
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


_CMP_OP_TO_FUNCTION = {
    ast3.Eq: lambda x, y: x == y,
    ast3.NotEq: lambda x, y: x != y,
    ast3.Lt: lambda x, y: x < y,
    ast3.LtE: lambda x, y: x <= y,
    ast3.Gt: lambda x, y: x > y,
    ast3.GtE: lambda x, y: x >= y,
    ast3.Is: lambda x, y: x is y,
    ast3.IsNot: lambda x, y: x is not y,
    ast3.In: lambda x, y: x in y,
    ast3.NotIn: lambda x, y: x not in y,
}


class _NameExtractor(ast3.NodeVisitor):
    """Extract names from a stub module."""

    def __init__(self, env: Env, module_name: ModulePath) -> None:
        self.env = env
        self.module_name = module_name

    def visit_Module(self, node: ast3.Module) -> List[NameInfo]:
        return [info for child in node.body for info in self.visit(child)]

    def visit_FunctionDef(self, node: ast3.FunctionDef) -> Iterable[NameInfo]:
        yield NameInfo(node.name, not node.name.startswith("_"), node)

    def visit_AsyncFunctionDef(self, node: ast3.AsyncFunctionDef) -> Iterable[NameInfo]:
        yield NameInfo(node.name, not node.name.startswith("_"), node)

    def visit_ClassDef(self, node: ast3.ClassDef) -> Iterable[NameInfo]:
        children = [info for child in node.body for info in self.visit(child)]
        child_dict = {info.name: info for info in children}
        yield NameInfo(node.name, not node.name.startswith("_"), node, child_dict)

    def visit_Assign(self, node: ast3.Assign) -> Iterable[NameInfo]:
        for target in node.targets:
            if not isinstance(target, ast3.Name):
                raise InvalidStub(
                    f"Assignment should only be to a simple name: {ast3.dump(node)}"
                )
            yield NameInfo(target.id, not target.id.startswith("_"), node)

    def visit_AnnAssign(self, node: ast3.AnnAssign) -> Iterable[NameInfo]:
        target = node.target
        if not isinstance(target, ast3.Name):
            raise InvalidStub(
                f"Assignment should only be to a simple name: {ast3.dump(node)}"
            )
        yield NameInfo(target.id, not target.id.startswith("_"), node)

    def visit_If(self, node: ast3.If) -> Iterable[NameInfo]:
        visitor = _LiteralEvalVisitor(self.env)
        value = visitor.visit(node.test)
        if value:
            for stmt in node.body:
                yield from self.visit(stmt)
        else:
            for stmt in node.orelse:
                yield from self.visit(stmt)

    def visit_Import(self, node: ast3.Import) -> Iterable[NameInfo]:
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

    def visit_ImportFrom(self, node: ast3.ImportFrom) -> Iterable[NameInfo]:
        module: Tuple[str, ...]
        if node.module is None:
            module = ()
        else:
            module = tuple(node.module.split("."))
        if node.level == 0:
            source_module = ModulePath(module)
        else:
            source_module = ModulePath(self.module_name[: -node.level] + module)
        for alias in node.names:
            if alias.asname is not None:
                is_exported = not alias.asname.startswith("_")
                yield NameInfo(
                    alias.asname, is_exported, ImportedName(source_module, alias.name)
                )
            elif alias.name == "*":
                name_dict = get_stub_names(
                    ".".join(source_module),
                    version=self.env.version,
                    platform=self.env.platform,
                    typeshed_dir=self.env.typeshed_dir,
                )
                if name_dict is None:
                    log.warning(
                        f"could not import {source_module} in {self.module_name} with "
                        f"{self.env}"
                    )
                    continue
                for name, info in name_dict.items():
                    if info.is_exported:
                        yield NameInfo(name, True, ImportedName(source_module, name))
            else:
                yield NameInfo(
                    alias.name, False, ImportedName(source_module, alias.name)
                )

    def visit_Expr(self, node: ast3.Expr) -> Iterable[NameInfo]:
        if not isinstance(node.value, (ast3.Ellipsis, ast3.Str)):
            raise InvalidStub(f"Cannot handle node {ast3.dump(node)}")
        return []

    def visit_Pass(self, node: ast3.Pass) -> Iterable[NameInfo]:
        return []

    def generic_visit(self, node: ast3.AST) -> NoReturn:
        raise InvalidStub(f"Cannot handle node {ast3.dump(node)}")


class _LiteralEvalVisitor(ast3.NodeVisitor):
    def __init__(self, env: Env) -> None:
        self.env = env

    def visit_Num(self, node: ast3.Num) -> Union[int, float]:
        return node.n

    def visit_Str(self, node: ast3.Str) -> str:
        return node.s

    def visit_Index(self, node: ast3.Index) -> int:
        return self.visit(node.value)

    def visit_Tuple(self, node: ast3.Tuple) -> Tuple[Any, ...]:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_Subscript(self, node: ast3.Subscript) -> Any:
        value = self.visit(node.value)
        slc = self.visit(node.slice)
        return value[slc]

    def visit_Compare(self, node: ast3.Compare) -> bool:
        if len(node.ops) != 1:
            raise InvalidStub(f"Cannot evaluate chained comparison {ast3.dump(node)}")
        fn = _CMP_OP_TO_FUNCTION[type(node.ops[0])]
        return fn(self.visit(node.left), self.visit(node.comparators[0]))

    def visit_BoolOp(self, node: ast3.BoolOp) -> bool:
        for val_node in node.values:
            val = self.visit(val_node)
            if (isinstance(node.op, ast3.Or) and val) or (
                isinstance(node.op, ast3.And) and not val
            ):
                return val
        return val

    def visit_Slice(self, node: ast3.Slice) -> slice:
        lower = self.visit(node.lower) if node.lower is not None else None
        upper = self.visit(node.upper) if node.upper is not None else None
        step = self.visit(node.step) if node.step is not None else None
        return slice(lower, upper, step)

    def visit_Attribute(self, node: ast3.Attribute) -> Any:
        val = node.value
        if not isinstance(val, ast3.Name):
            raise InvalidStub(f"Invalid code in stub: {ast3.dump(node)}")
        if val.id != "sys":
            raise InvalidStub(
                f"Attribute access must be on the sys module: {ast3.dump(node)}"
            )
        if node.attr == "platform":
            return self.env.platform
        elif node.attr == "version_info":
            return self.env.version
        else:
            raise InvalidStub(f"Invalid attribute on {ast3.dump(node)}")

    def generic_visit(self, node: ast3.AST) -> NoReturn:
        raise InvalidStub(f"Cannot evaluate node {ast3.dump(node)}")
