# area: dunder_dispatch
# hypothesis: A class whose __len__ is declared only as an annotation must be rejected by len() because CPython raises TypeError when the special method is looked up on the type, so accepting len(obj) is unsound.
# origin: runs/day10/parents/H_new/d8p_dunder_dispatch_annotation_only_call.py
# area: dunder_dispatch
# hypothesis: A class whose __len__ exists only as an annotation must be rejected by len(), because CPython looks special methods up on the type and raises TypeError, so a checker that accepts len(obj) is unsound.
from typing import Callable, reveal_type


class Sized:
    __len__: Callable[[], int]  # declared only, no method on the class

    def __init__(self, items: list[str]) -> None:
        self.items = items


class SizedOk:
    def __init__(self, items: list[str]) -> None:
        self.items = items

    def __len__(self) -> int:
        return len(self.items)


def probe_missing() -> str:
    s = Sized(['a', 'b'])
    try:
        n = len(s)  # expect-error: Sized has no __len__ on its type
        reveal_type(n)
    except TypeError:
        return 'TypeError'
    return 'len ok'


def probe_control() -> int:
    s = SizedOk(['a', 'b', 'c'])
    return len(s)


print(probe_missing())
print(probe_control())
