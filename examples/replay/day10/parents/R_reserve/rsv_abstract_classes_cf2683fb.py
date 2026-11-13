# area: abstract_classes
# hypothesis: A TypeIs[Source] guard accepts a runtime-registered class and narrows it to Source, while a static checker still rejects passing that same registered class where Source is expected.
# origin: runs/day9/parents/R_reserve/rsv_abstract_classes_5a90804c.py
# area: abstract_classes
# hypothesis: A TypeIs[Source] guard accepts a runtime-registered class and narrows it to Source, while a static checker still rejects passing that same registered class where Source is expected.
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeIs, assert_type, reveal_type


class Source(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...


class AttrSource(Source):
    name = 'attr'


@dataclass
class DataSource(Source):
    name: str = 'data'


class Fixed:
    @property
    def name(self) -> str:
        return 'fixed'


Source.register(Fixed)


def is_source(x: object) -> TypeIs[Source]:
    return isinstance(x, Source)


def load(x: AttrSource | Fixed) -> str:
    if is_source(x):
        reveal_type(x)
        return x.name
    return 'none'


def need_source(s: Source) -> str:
    return s.name


def bad(f: Fixed) -> str:
    return need_source(f)  # expect-error: Fixed is not statically a Source


assert_type(load(AttrSource()), str)
assert load(AttrSource()) == 'attr'
assert load(Fixed()) == 'fixed'
assert DataSource().name == 'data'
assert issubclass(Fixed, Source)
assert bad(Fixed()) == 'fixed'
