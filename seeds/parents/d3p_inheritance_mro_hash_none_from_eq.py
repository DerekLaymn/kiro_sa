# area: inheritance_mro
# hypothesis: A class that defines __eq__ but not __hash__ gets __hash__ = None at runtime; calling it raises TypeError and only pyright reports it (mypy and ty are silent). Vary: dataclass(eq=True), a subclass that restores __hash__, a set or dict-key use, a Hashable protocol argument.
# origin: runs/day2/out3 seed-67975a0c41c4 (pyright tests/samples/hashability3.py; runtime_miss, mypy and ty silent)
class A: ...


A().__hash__()


class B:
    def __eq__(self, value: object) -> bool:
        return True


B().__hash__()
