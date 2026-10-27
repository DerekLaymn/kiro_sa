from typing import Any, reveal_type


class Coerce:
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = "_" + name

    def __get__(self, obj: Any, owner: Any = None) -> int:
        if obj is None:
            return -1
        return getattr(obj, self.name)

    def __set__(self, obj: Any, value: str) -> None:
        setattr(obj, self.name, int(value))


class M:
    n = Coerce()


m = M()
m.n = "42"
reveal_type(m.n)
print(m.n + 1)
try:
    m.n = 5  # type: ignore
except ValueError:
    print("ValueError")
except TypeError:
    print("TypeError")
reveal_type(M.n)
print(M.n)
