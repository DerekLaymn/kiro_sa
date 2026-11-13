# area: inheritance_mro
# hypothesis: A class that defines __eq__ without __hash__ gets __hash__ = None at runtime, so it is not Hashable; pyright rejects Plain() and Sub() for a Hashable parameter, mypy and ty accept them (ty does reject a mutable dataclass).
# origin: results/bugs.md section 4 (seed-a43a619b6518, d3p_inheritance_mro_hash_none_from_eq__mut1_fdf751d0)
from collections.abc import Hashable


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


class Sub(Plain): ...


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


def need(x: Hashable) -> int:
    return hash(x)


need(Keyed())
for obj in (Plain(), Sub()):
    try:
        need(obj)
    except TypeError as exc:
        print(exc)
