# area: overloads
# explores: overloads on methods keyed by Literal keyword flags, overloaded classmethods returning Self,
# calling with a plain bool (the spec expands bool into Literal[True] | Literal[False] during overload evaluation)
from typing import Literal, Self, overload, reveal_type


class Parser:
    @overload
    def parse(self, raw: str, *, many: Literal[True]) -> list[int]: ...
    @overload
    def parse(self, raw: str, *, many: Literal[False] = ...) -> int: ...
    def parse(self, raw: str, *, many: bool = False) -> int | list[int]:
        if many:
            return [int(x) for x in raw.split(",")]
        return int(raw)

    @overload
    @classmethod
    def create(cls) -> Self: ...
    @overload
    @classmethod
    def create(cls, strict: bool) -> Self: ...
    @classmethod
    def create(cls, strict: bool = False) -> Self:
        return cls()


class StrictParser(Parser):
    pass


def with_flag(p: Parser, b: bool) -> None:
    print(p.parse("3", many=b))  # spec: bool is expanded to Literal[True] | Literal[False] -> int | list[int] (mypy rejects this)


p = StrictParser.create(True)
reveal_type(p)  # StrictParser
reveal_type(p.parse("1"))  # int
reveal_type(p.parse("1,2", many=True))  # list[int]
print(p.parse("1"), p.parse("1,2", many=True))
with_flag(p, True)
