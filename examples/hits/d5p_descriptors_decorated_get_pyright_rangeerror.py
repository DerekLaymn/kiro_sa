# area: descriptors_properties
# hypothesis: A plain function defined in the class body (no self) decorates both __get__ and __set__ of a descriptor; pyright 1.1.414 dies with RangeError 'Maximum call stack size exceeded' (typeUtils.ts / retainTypeAlias) while mypy and ty report ordinary arg-type errors and CPython runs the program. Vary: decorate only __set__, a staticmethod or classmethod decorator, a decorator returning a descriptor, __delete__.
# origin: generated program of the campaign (not kept) (seed-947242212886); results/days/day4-report.md section 5 item 1
class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42

    def wrap(fn):
        return fn

    @wrap
    def __set__(self, obj: object, value: int) -> None:
        print("set", value)


class Host:
    attr = Desc()


h = Host()
print(h.attr, Desc.__get__(Desc(), None, Host))
Desc.__set__(Desc(), h, 5)
