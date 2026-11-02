import sys
from typediff.typenorm import normalize, relation

PAIRS = [
    ("str", 'str & ~Literal["a"]'), ("case.B", "B & ~A"), ("int", "int & ~Literal[1] & ~Literal[True]"),
    ("str", "str & ~AlwaysFalsy"), ("bool", "bool & Unknown"), ("None", "Unknown & None"),
    ("case.B | case.C", "(B & ~A) | (C & ~A)"), ("str", "LiteralString"), ("list[str]", "list[LiteralString]"),
    ("type", "<class 'Foo'>"), ("type[object]", "type"), ("int", "Never"), ("bool", "Never"),
    ("tuple[Any, int]", "tuple[Unknown, int]"), ("case.Foo", "Foo"),
]
for a, b in PAIRS:
    na, nb = normalize(a, "case"), normalize(b, "case")
    print(f"{a!r:36} vs {b!r:44} -> {relation(na, nb).value:14} comparable={na.comparable},{nb.comparable} text={na.text!r} | {nb.text!r}")
