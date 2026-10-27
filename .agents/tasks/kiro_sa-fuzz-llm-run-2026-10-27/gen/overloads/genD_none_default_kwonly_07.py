from typing import overload, reveal_type


@overload
def open_(path: str) -> str: ...
@overload
def open_(path: str, *, binary: bool) -> str | bytes: ...
@overload
def open_(path: str, *, binary: None = None, enc: str) -> str: ...
def open_(path: str, *, binary: bool | None = None, enc: str = "u") -> str | bytes:
    return path.encode() if binary else path


def f(flag: bool, **kw: bool) -> None:
    reveal_type(open_("a"))
    reveal_type(open_("a", binary=flag))
    reveal_type(open_("a", binary=None, enc="x"))
    reveal_type(open_("a", binary=True))


f(True)
print(open_("a"), open_("b", binary=True), open_("c", enc="z"))
