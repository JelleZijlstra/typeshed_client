from typing import Any, Callable, Dict, List, NamedTuple, Text, Tuple

class Event(NamedTuple):
    time: float
    priority: Any
    action: Callable[..., Any]
    argument: Tuple[Any, ...]
    kwargs: Dict[Text, Any]

class scheduler:
    def __init__(
        self, timefunc: Callable[[], float], delayfunc: Callable[[float], None]
    ) -> None: ...
    def enterabs(
        self,
        time: float,
        priority: Any,
        action: Callable[..., Any],
        argument: Tuple[Any, ...],
    ) -> Event: ...
    def enter(
        self,
        delay: float,
        priority: Any,
        action: Callable[..., Any],
        argument: Tuple[Any, ...],
    ) -> Event: ...
    def run(self) -> None: ...
    def cancel(self, event: Event) -> None: ...
    def empty(self) -> bool: ...
    @property
    def queue(self) -> List[Event]: ...
