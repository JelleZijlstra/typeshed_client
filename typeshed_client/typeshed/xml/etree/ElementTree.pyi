import sys
from _collections_abc import dict_keys
from _typeshed import FileDescriptorOrPath, ReadableBuffer, SupportsRead, SupportsWrite
from collections.abc import Callable, Generator, ItemsView, Iterable, Iterator, Mapping, Sequence
from typing import Any, TypeVar, overload
from typing_extensions import Literal, SupportsIndex, TypeAlias, TypeGuard

__all__ = [
    "Comment",
    "dump",
    "Element",
    "ElementTree",
    "fromstring",
    "fromstringlist",
    "iselement",
    "iterparse",
    "parse",
    "ParseError",
    "PI",
    "ProcessingInstruction",
    "QName",
    "SubElement",
    "tostring",
    "tostringlist",
    "TreeBuilder",
    "VERSION",
    "XML",
    "XMLID",
    "XMLParser",
    "XMLPullParser",
    "register_namespace",
]

if sys.version_info >= (3, 8):
    __all__ += ["C14NWriterTarget", "canonicalize"]

if sys.version_info >= (3, 9):
    __all__ += ["indent"]

_T = TypeVar("_T")
_FileRead: TypeAlias = FileDescriptorOrPath | SupportsRead[bytes] | SupportsRead[str]
_FileWriteC14N: TypeAlias = FileDescriptorOrPath | SupportsWrite[bytes]
_FileWrite: TypeAlias = _FileWriteC14N | SupportsWrite[str]

VERSION: str

class ParseError(SyntaxError):
    code: int
    position: tuple[int, int]

# In reality it works based on `.tag` attribute duck typing.
def iselement(element: object) -> TypeGuard[Element]: ...

if sys.version_info >= (3, 8):
    @overload
    def canonicalize(
        xml_data: str | ReadableBuffer | None = ...,
        *,
        out: None = ...,
        from_file: _FileRead | None = ...,
        with_comments: bool = ...,
        strip_text: bool = ...,
        rewrite_prefixes: bool = ...,
        qname_aware_tags: Iterable[str] | None = ...,
        qname_aware_attrs: Iterable[str] | None = ...,
        exclude_attrs: Iterable[str] | None = ...,
        exclude_tags: Iterable[str] | None = ...,
    ) -> str: ...
    @overload
    def canonicalize(
        xml_data: str | ReadableBuffer | None = ...,
        *,
        out: SupportsWrite[str],
        from_file: _FileRead | None = ...,
        with_comments: bool = ...,
        strip_text: bool = ...,
        rewrite_prefixes: bool = ...,
        qname_aware_tags: Iterable[str] | None = ...,
        qname_aware_attrs: Iterable[str] | None = ...,
        exclude_attrs: Iterable[str] | None = ...,
        exclude_tags: Iterable[str] | None = ...,
    ) -> None: ...

class Element:
    tag: str
    attrib: dict[str, str]
    text: str | None
    tail: str | None
    def __init__(self, tag: str | Callable[..., Element], attrib: dict[str, str] = ..., **extra: str) -> None: ...
    def append(self, __subelement: Element) -> None: ...
    def clear(self) -> None: ...
    def extend(self, __elements: Iterable[Element]) -> None: ...
    def find(self, path: str, namespaces: dict[str, str] | None = None) -> Element | None: ...
    def findall(self, path: str, namespaces: dict[str, str] | None = None) -> list[Element]: ...
    @overload
    def findtext(self, path: str, default: None = ..., namespaces: dict[str, str] | None = ...) -> str | None: ...
    @overload
    def findtext(self, path: str, default: _T, namespaces: dict[str, str] | None = ...) -> _T | str: ...
    @overload
    def get(self, key: str, default: None = ...) -> str | None: ...
    @overload
    def get(self, key: str, default: _T) -> str | _T: ...
    def insert(self, __index: int, __subelement: Element) -> None: ...
    def items(self) -> ItemsView[str, str]: ...
    def iter(self, tag: str | None = None) -> Generator[Element, None, None]: ...
    def iterfind(self, path: str, namespaces: dict[str, str] | None = None) -> Generator[Element, None, None]: ...
    def itertext(self) -> Generator[str, None, None]: ...
    def keys(self) -> dict_keys[str, str]: ...
    # makeelement returns the type of self in Python impl, but not in C impl
    def makeelement(self, __tag: str, __attrib: dict[str, str]) -> Element: ...
    def remove(self, __subelement: Element) -> None: ...
    def set(self, __key: str, __value: str) -> None: ...
    def __copy__(self) -> Element: ...  # returns the type of self in Python impl, but not in C impl
    def __deepcopy__(self, __memo: Any) -> Element: ...  # Only exists in C impl
    def __delitem__(self, __i: SupportsIndex | slice) -> None: ...
    @overload
    def __getitem__(self, __i: SupportsIndex) -> Element: ...
    @overload
    def __getitem__(self, __s: slice) -> list[Element]: ...
    def __len__(self) -> int: ...
    # Doesn't actually exist at runtime, but instance of the class are indeed iterable due to __getitem__.
    def __iter__(self) -> Iterator[Element]: ...
    @overload
    def __setitem__(self, __i: SupportsIndex, __o: Element) -> None: ...
    @overload
    def __setitem__(self, __s: slice, __o: Iterable[Element]) -> None: ...
    if sys.version_info < (3, 9):
        def getchildren(self) -> list[Element]: ...
        def getiterator(self, tag: str | None = ...) -> list[Element]: ...

def SubElement(parent: Element, tag: str, attrib: dict[str, str] = ..., **extra: str) -> Element: ...
def Comment(text: str | None = None) -> Element: ...
def ProcessingInstruction(target: str, text: str | None = None) -> Element: ...

PI: Callable[..., Element]

class QName:
    text: str
    def __init__(self, text_or_uri: str, tag: str | None = None) -> None: ...
    def __lt__(self, other: QName | str) -> bool: ...
    def __le__(self, other: QName | str) -> bool: ...
    def __gt__(self, other: QName | str) -> bool: ...
    def __ge__(self, other: QName | str) -> bool: ...
    def __eq__(self, other: object) -> bool: ...

class ElementTree:
    def __init__(self, element: Element | None = None, file: _FileRead | None = None) -> None: ...
    def getroot(self) -> Element | Any: ...
    def parse(self, source: _FileRead, parser: XMLParser | None = None) -> Element: ...
    def iter(self, tag: str | None = None) -> Generator[Element, None, None]: ...
    if sys.version_info < (3, 9):
        def getiterator(self, tag: str | None = ...) -> list[Element]: ...

    def find(self, path: str, namespaces: dict[str, str] | None = None) -> Element | None: ...
    @overload
    def findtext(self, path: str, default: None = ..., namespaces: dict[str, str] | None = ...) -> str | None: ...
    @overload
    def findtext(self, path: str, default: _T, namespaces: dict[str, str] | None = ...) -> _T | str: ...
    def findall(self, path: str, namespaces: dict[str, str] | None = None) -> list[Element]: ...
    def iterfind(self, path: str, namespaces: dict[str, str] | None = None) -> Generator[Element, None, None]: ...
    def write(
        self,
        file_or_filename: _FileWrite,
        encoding: str | None = None,
        xml_declaration: bool | None = None,
        default_namespace: str | None = None,
        method: str | None = None,
        *,
        short_empty_elements: bool = True,
    ) -> None: ...
    def write_c14n(self, file: _FileWriteC14N) -> None: ...

def register_namespace(prefix: str, uri: str) -> None: ...

if sys.version_info >= (3, 8):
    @overload
    def tostring(
        element: Element,
        encoding: None = ...,
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> bytes: ...
    @overload
    def tostring(
        element: Element,
        encoding: Literal["unicode"],
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> str: ...
    @overload
    def tostring(
        element: Element,
        encoding: str,
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> Any: ...
    @overload
    def tostringlist(
        element: Element,
        encoding: None = ...,
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> list[bytes]: ...
    @overload
    def tostringlist(
        element: Element,
        encoding: Literal["unicode"],
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> list[str]: ...
    @overload
    def tostringlist(
        element: Element,
        encoding: str,
        method: str | None = ...,
        *,
        xml_declaration: bool | None = ...,
        default_namespace: str | None = ...,
        short_empty_elements: bool = ...,
    ) -> list[Any]: ...

else:
    @overload
    def tostring(
        element: Element, encoding: None = ..., method: str | None = ..., *, short_empty_elements: bool = ...
    ) -> bytes: ...
    @overload
    def tostring(
        element: Element, encoding: Literal["unicode"], method: str | None = ..., *, short_empty_elements: bool = ...
    ) -> str: ...
    @overload
    def tostring(element: Element, encoding: str, method: str | None = ..., *, short_empty_elements: bool = ...) -> Any: ...
    @overload
    def tostringlist(
        element: Element, encoding: None = ..., method: str | None = ..., *, short_empty_elements: bool = ...
    ) -> list[bytes]: ...
    @overload
    def tostringlist(
        element: Element, encoding: Literal["unicode"], method: str | None = ..., *, short_empty_elements: bool = ...
    ) -> list[str]: ...
    @overload
    def tostringlist(
        element: Element, encoding: str, method: str | None = ..., *, short_empty_elements: bool = ...
    ) -> list[Any]: ...

def dump(elem: Element) -> None: ...

if sys.version_info >= (3, 9):
    def indent(tree: Element | ElementTree, space: str = "  ", level: int = 0) -> None: ...

def parse(source: _FileRead, parser: XMLParser | None = None) -> ElementTree: ...
def iterparse(
    source: _FileRead, events: Sequence[str] | None = None, parser: XMLParser | None = None
) -> Iterator[tuple[str, Any]]: ...

class XMLPullParser:
    def __init__(self, events: Sequence[str] | None = None, *, _parser: XMLParser | None = None) -> None: ...
    def feed(self, data: str | ReadableBuffer) -> None: ...
    def close(self) -> None: ...
    # Second element in the tuple could be `Element`, `tuple[str, str]` or `None`.
    # Use `Any` to avoid false-positive errors.
    def read_events(self) -> Iterator[tuple[str, Any]]: ...

def XML(text: str | ReadableBuffer, parser: XMLParser | None = None) -> Element: ...
def XMLID(text: str | ReadableBuffer, parser: XMLParser | None = None) -> tuple[Element, dict[str, Element]]: ...

# This is aliased to XML in the source.
fromstring = XML

def fromstringlist(sequence: Sequence[str | ReadableBuffer], parser: XMLParser | None = None) -> Element: ...

# This type is both not precise enough and too precise. The TreeBuilder
# requires the elementfactory to accept tag and attrs in its args and produce
# some kind of object that has .text and .tail properties.
# I've chosen to constrain the ElementFactory to always produce an Element
# because that is how almost everyone will use it.
# Unfortunately, the type of the factory arguments is dependent on how
# TreeBuilder is called by client code (they could pass strs, bytes or whatever);
# but we don't want to use a too-broad type, or it would be too hard to write
# elementfactories.
_ElementFactory: TypeAlias = Callable[[Any, dict[Any, Any]], Element]

class TreeBuilder:
    if sys.version_info >= (3, 8):
        # comment_factory can take None because passing None to Comment is not an error
        def __init__(
            self,
            element_factory: _ElementFactory | None = ...,
            *,
            comment_factory: Callable[[str | None], Element] | None = ...,
            pi_factory: Callable[[str, str | None], Element] | None = ...,
            insert_comments: bool = ...,
            insert_pis: bool = ...,
        ) -> None: ...
        insert_comments: bool
        insert_pis: bool
    else:
        def __init__(self, element_factory: _ElementFactory | None = ...) -> None: ...

    def close(self) -> Element: ...
    def data(self, __data: str) -> None: ...
    # tag and attrs are passed to the element_factory, so they could be anything
    # depending on what the particular factory supports.
    def start(self, __tag: Any, __attrs: dict[Any, Any]) -> Element: ...
    def end(self, __tag: str) -> Element: ...
    if sys.version_info >= (3, 8):
        # These two methods have pos-only parameters in the C implementation
        def comment(self, __text: str | None) -> Element: ...
        def pi(self, __target: str, __text: str | None = ...) -> Element: ...

if sys.version_info >= (3, 8):
    class C14NWriterTarget:
        def __init__(
            self,
            write: Callable[[str], object],
            *,
            with_comments: bool = False,
            strip_text: bool = False,
            rewrite_prefixes: bool = False,
            qname_aware_tags: Iterable[str] | None = None,
            qname_aware_attrs: Iterable[str] | None = None,
            exclude_attrs: Iterable[str] | None = None,
            exclude_tags: Iterable[str] | None = None,
        ) -> None: ...
        def data(self, data: str) -> None: ...
        def start_ns(self, prefix: str, uri: str) -> None: ...
        def start(self, tag: str, attrs: Mapping[str, str]) -> None: ...
        def end(self, tag: str) -> None: ...
        def comment(self, text: str) -> None: ...
        def pi(self, target: str, data: str) -> None: ...

class XMLParser:
    parser: Any
    target: Any
    # TODO-what is entity used for???
    entity: Any
    version: str
    if sys.version_info >= (3, 8):
        def __init__(self, *, target: Any = ..., encoding: str | None = ...) -> None: ...
    else:
        def __init__(self, html: int = ..., target: Any = ..., encoding: str | None = ...) -> None: ...
        def doctype(self, __name: str, __pubid: str, __system: str) -> None: ...

    def close(self) -> Any: ...
    def feed(self, __data: str | ReadableBuffer) -> None: ...
