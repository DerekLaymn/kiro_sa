# area: dunder_dispatch
# hypothesis: CPython looks special methods up on the type, so an instance-assigned __len__ is ignored by len(), __getattr__ never supplies dunders for indexing or with, an annotation-only __iter__ has no runtime method, and an inherited __call__ is used while an instance-level __call__ is not.
# origin: llm
# area: dunder_dispatch
# hypothesis: CPython looks special methods up on the type, so an instance-assigned __len__ is ignored by len(), __getattr__ never supplies dunders for indexing or with, an annotation-only __iter__ has no runtime method, and an inherited __call__ is used while an instance-level __call__ is not.
from collections.abc import Callable, Iterator
from typing import reveal_type


class AnnOnly:
    __iter__: Callable[[], Iterator[int]]  # annotation only, no value


class InstanceDunder:
    def __init__(self) -> None:
        self.__len__ = lambda: 5  # instance attribute, ignored by len()


class Fallback:
    def __getattr__(self, name: str) -> int:
        return 42


class Base:
    def __call__(self) -> str:
        return 'base'


class Child(Base):
    pass


def enter_fallback() -> None:
    with Fallback():  # expect-error: no __enter__ on the type
        pass


def try_it(label: str, thunk: Callable[[], object]) -> None:
    try:
        print(label, 'ok', thunk())
    except (TypeError, AttributeError) as exc:
        print(label, 'error', type(exc).__name__)


try_it('iter', lambda: iter(AnnOnly()))
try_it('len', lambda: len(InstanceDunder()))  # expect-error: instance __len__ ignored
try_it('getitem', lambda: Fallback()[0])  # expect-error: __getattr__ not used for dunders
try_it('attr', lambda: Fallback().anything)
try_it('enter', enter_fallback)
reveal_type(Child()())
try_it('child', lambda: Child()())
b = Base()
b.__call__ = lambda: 'instance'  # expect-error: cannot assign to a method
try_it('instcall', lambda: b())
