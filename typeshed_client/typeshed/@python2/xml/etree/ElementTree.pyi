from _typeshed import FileDescriptor
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Generator,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    MutableSequence,
    Sequence,
    Text,
    Tuple,
    TypeVar,
    Union,
    overload,
)

VERSION: str

class ParseError(SyntaxError):
    code: int
    position: Tuple[int, int]

def iselement(element: object) -> bool: ...

_T = TypeVar("_T")

# Type for parser inputs. Parser will accept any unicode/str/bytes and coerce,
# and this is true in py2 and py3 (even fromstringlist() in python3 can be
# called with a heterogeneous list)
_parser_input_type = Union[bytes, Text]

# Type for individual tag/attr/ns/text values in args to most functions.
# In py2, the library accepts str or unicode everywhere and coerces
# aggressively.
# In py3, bytes is not coerced to str and so use of bytes is probably an error,
# so we exclude it. (why? the parser never produces bytes when it parses XML,
# so e.g., element.get(b'name') will always return None for parsed XML, even if
# there is a 'name' attribute.)
_str_argument_type = Union[str, Text]

# Type for return values from individual tag/attr/text values
# in python2, if the tag/attribute/text wasn't decode-able as ascii, it
# comes out as a unicode string; otherwise it comes out as str. (see
# _fixtext function in the source). Client code knows best:
_str_result_type = Any

_file_or_filename = Union[Text, FileDescriptor, IO[Any]]

class Element(MutableSequence[Element]):
    tag: _str_result_type
    attrib: Dict[_str_result_type, _str_result_type]
    text: _str_result_type | None
    tail: _str_result_type | None
    def __init__(
        self,
        tag: _str_argument_type | Callable[..., Element],
        attrib: Dict[_str_argument_type, _str_argument_type] = ...,
        **extra: _str_argument_type,
    ) -> None: ...
    def append(self, __subelement: Element) -> None: ...
    def clear(self) -> None: ...
    def extend(self, __elements: Iterable[Element]) -> None: ...
    def find(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> Element | None: ...
    def findall(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> List[Element]: ...
    @overload
    def findtext(
        self,
        path: _str_argument_type,
        default: None = ...,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> _str_result_type | None: ...
    @overload
    def findtext(
        self,
        path: _str_argument_type,
        default: _T,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> _T | _str_result_type: ...
    @overload
    def get(
        self, key: _str_argument_type, default: None = ...
    ) -> _str_result_type | None: ...
    @overload
    def get(self, key: _str_argument_type, default: _T) -> _str_result_type | _T: ...
    def insert(self, __index: int, __element: Element) -> None: ...
    def items(self) -> ItemsView[_str_result_type, _str_result_type]: ...
    def iter(
        self, tag: _str_argument_type | None = ...
    ) -> Generator[Element, None, None]: ...
    def iterfind(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> Generator[Element, None, None]: ...
    def itertext(self) -> Generator[_str_result_type, None, None]: ...
    def keys(self) -> KeysView[_str_result_type]: ...
    def makeelement(
        self,
        __tag: _str_argument_type,
        __attrib: Dict[_str_argument_type, _str_argument_type],
    ) -> Element: ...
    def remove(self, __subelement: Element) -> None: ...
    def set(self, __key: _str_argument_type, __value: _str_argument_type) -> None: ...
    def __delitem__(self, i: int | slice) -> None: ...
    @overload
    def __getitem__(self, i: int) -> Element: ...
    @overload
    def __getitem__(self, s: slice) -> MutableSequence[Element]: ...
    def __len__(self) -> int: ...
    @overload
    def __setitem__(self, i: int, o: Element) -> None: ...
    @overload
    def __setitem__(self, s: slice, o: Iterable[Element]) -> None: ...
    def getchildren(self) -> List[Element]: ...
    def getiterator(self, tag: _str_argument_type | None = ...) -> List[Element]: ...

def SubElement(
    parent: Element,
    tag: _str_argument_type,
    attrib: Dict[_str_argument_type, _str_argument_type] = ...,
    **extra: _str_argument_type,
) -> Element: ...
def Comment(text: _str_argument_type | None = ...) -> Element: ...
def ProcessingInstruction(
    target: _str_argument_type, text: _str_argument_type | None = ...
) -> Element: ...

PI: Callable[..., Element]

class QName:
    text: str
    def __init__(
        self, text_or_uri: _str_argument_type, tag: _str_argument_type | None = ...
    ) -> None: ...

class ElementTree:
    def __init__(
        self, element: Element | None = ..., file: _file_or_filename | None = ...
    ) -> None: ...
    def getroot(self) -> Element: ...
    def parse(
        self, source: _file_or_filename, parser: XMLParser | None = ...
    ) -> Element: ...
    def iter(
        self, tag: _str_argument_type | None = ...
    ) -> Generator[Element, None, None]: ...
    def getiterator(self, tag: _str_argument_type | None = ...) -> List[Element]: ...
    def find(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> Element | None: ...
    @overload
    def findtext(
        self,
        path: _str_argument_type,
        default: None = ...,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> _str_result_type | None: ...
    @overload
    def findtext(
        self,
        path: _str_argument_type,
        default: _T,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> _T | _str_result_type: ...
    def findall(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> List[Element]: ...
    def iterfind(
        self,
        path: _str_argument_type,
        namespaces: Dict[_str_argument_type, _str_argument_type] | None = ...,
    ) -> Generator[Element, None, None]: ...
    def write(
        self,
        file_or_filename: _file_or_filename,
        encoding: str | None = ...,
        xml_declaration: bool | None = ...,
        default_namespace: _str_argument_type | None = ...,
        method: str | None = ...,
    ) -> None: ...
    def write_c14n(self, file: _file_or_filename) -> None: ...

def register_namespace(prefix: _str_argument_type, uri: _str_argument_type) -> None: ...
def tostring(
    element: Element, encoding: str | None = ..., method: str | None = ...
) -> bytes: ...
def tostringlist(
    element: Element, encoding: str | None = ..., method: str | None = ...
) -> List[bytes]: ...
def dump(elem: Element) -> None: ...
def parse(source: _file_or_filename, parser: XMLParser | None = ...) -> ElementTree: ...
def iterparse(
    source: _file_or_filename,
    events: Sequence[str] | None = ...,
    parser: XMLParser | None = ...,
) -> Iterator[Tuple[str, Any]]: ...
def XML(text: _parser_input_type, parser: XMLParser | None = ...) -> Element: ...
def XMLID(
    text: _parser_input_type, parser: XMLParser | None = ...
) -> Tuple[Element, Dict[_str_result_type, Element]]: ...

# This is aliased to XML in the source.
fromstring = XML

def fromstringlist(
    sequence: Sequence[_parser_input_type], parser: XMLParser | None = ...
) -> Element: ...

# This type is both not precise enough and too precise. The TreeBuilder
# requires the elementfactory to accept tag and attrs in its args and produce
# some kind of object that has .text and .tail properties.
# I've chosen to constrain the ElementFactory to always produce an Element
# because that is how almost everyone will use it.
# Unfortunately, the type of the factory arguments is dependent on how
# TreeBuilder is called by client code (they could pass strs, bytes or whatever);
# but we don't want to use a too-broad type, or it would be too hard to write
# elementfactories.
_ElementFactory = Callable[[Any, Dict[Any, Any]], Element]

class TreeBuilder:
    def __init__(self, element_factory: _ElementFactory | None = ...) -> None: ...
    def close(self) -> Element: ...
    def data(self, __data: _parser_input_type) -> None: ...
    def start(
        self,
        __tag: _parser_input_type,
        __attrs: Dict[_parser_input_type, _parser_input_type],
    ) -> Element: ...
    def end(self, __tag: _parser_input_type) -> Element: ...

class XMLParser:
    parser: Any
    target: Any
    # TODO-what is entity used for???
    entity: Any
    version: str
    def __init__(
        self, html: int = ..., target: Any = ..., encoding: str | None = ...
    ) -> None: ...
    def doctype(self, __name: str, __pubid: str, __system: str) -> None: ...
    def close(self) -> Any: ...
    def feed(self, __data: _parser_input_type) -> None: ...
