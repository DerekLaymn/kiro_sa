# area: descriptors_properties
# hypothesis: A self-less decorator that returns a different wrapper function, applied only to __delete__, should leave the descriptor's __delete__ checkable with ordinary arg-type errors, and CPython should run the wrapped method.
# origin: runs/day8/parents/A_pyright_range/d5p_descriptors_one_decorator_dunders_pyright_rangeerror.py
# area: descriptors_properties
# hypothesis: A self-less class-body decorator that returns a new wrapper, applied only to __delete__, yields a descriptor whose __delete__ is checked with ordinary arg-type rules, and CPython runs the wrapped method.
class Desc:
    def wrap(fn):
        def inner(self, obj: object) -> None:
            print('before delete')
            fn(self, obj)
        return inner

    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42

    def __set__(self, obj: object, value: int) -> None:
        print('set', value)

    @wrap
    def __delete__(self, obj: object) -> None:
        print('delete')


class Host:
    attr = Desc()


h = Host()
print(h.attr)
Desc.__set__(Desc(), h, 5)
Desc.__delete__(Desc(), h)
try:
    Desc.__delete__(Desc(), h, 1)  # expect-error: too many arguments
except TypeError as exc:
    print('runtime:', type(exc).__name__)
