# area: descriptors_properties
# hypothesis: One class-body decorator without self (deco) applied to both __get__ and __set__, plus an undecorated __delete__, still kills pyright 1.1.414 with RangeError 'Maximum call stack size exceeded' (typeUtils.ts); mypy and ty only report arg-type errors on the decorated dunders and CPython runs the program. Smaller than d5p_descriptors_decorated_get_pyright_rangeerror (one decorator instead of two). Vary: decorate only __delete__, a decorator that returns a different function, a descriptor on a dataclass field.
# origin: runs/day5/gen/descriptors_properties/d5p_descriptors_decorated_get_pyright_rangeerror__mut0_655241a2.py (seed-3ec974e3a5b4); campaign/day5-morning.md section 1
class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42

    @deco
    def __set__(self, obj: object, value: int) -> None:
        print('set', value)

    def __delete__(self, obj: object) -> None:
        print('delete')


class Host:
    attr = Desc()


h = Host()
print(h.attr)
Desc.__set__(Desc(), h, 5)
Desc.__delete__(Desc(), h)
