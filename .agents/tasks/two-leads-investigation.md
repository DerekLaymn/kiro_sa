# Two leads investigation

## Summary
- Lead (b) `Model.__replace__`: VERSION/CONFIG SKEW (harness noise), high confidence. Not a ty bug.
- Lead (a) metaclass ClassVar vs declared-only attribute: ASK AS QUESTION (low-priority), medium-low confidence. Not confirmed as a bug, not found as a duplicate.

## Lead (b)
Seed `seeds/harvested/gradual_any/ty__call__replace__9.py` comes from ruff mdtest `call/replace.md` block 9. In ruff main, that block sits under "Before Python 3.13" with `python-version = "3.12"`. The harvest dropped the TOML, so we ran it at 3.13. At 3.13, the same mdtest ("Dataclass transforms") says `__replace__` is synthesized for dataclass_transform classes ([source](https://raw.githubusercontent.com/astral-sh/ruff/main/crates/ty_python_semantic/resources/mdtest/call/replace.md)).
My run with `ty check --python-version 3.13` on a dataclass_transform class and `M.__replace__` was silent, as expected. mypy and pyright are also silent. CPython 3.13 does not add `__replace__` to a plain dataclass_transform class, but dataclass_transform classes are not dataclasses by themselves, so the runtime AttributeError reflects the undecorated stub class. This is a model of the checker's synthesized behavior, not a miss.
Not verified: running ty with `--python-version 3.12` (not run; the mdtest says it errors), and ty releases after 0.0.84.
Fix for the harness: have the harvester read `[environment] python-version` from mdtest TOML and pass it through, or skip blocks with a non-default version.

## Lead (a)
Repro (a.py in /tmp/l, run on my machine):

| variant | ty 0.0.84 | pyright 1.1.414 | mypy 2.4.0 | CPython |
|---|---|---|---|---|
| `eggs: str` (declared only) | str | str | int | 42 (int, from metaclass) |
| `eggs: str = 'x'` | str | str | int | 'x' (class dict wins over the non-data metaclass attribute) |
| `eggs: ClassVar[str] = 'x'` | str | str | str | 'x' |

Only the first row is questionable. In the second row, mypy's `int` is arguably wrong and ty/pyright are right. In the first row the runtime does give the metaclass value, because nothing is in `Foo.__dict__`.
Accused tool's side: a bare `eggs: str` is an instance-variable declaration. The typing spec does not define lookup order between a metaclass attribute and a declared-only instance variable on class-object access, and ty/pyright let the class-level declared type win. Mdtests I did not read may encode this deliberately. This is an edge case with an unusual metaclass and class clash. The mypy test name (`testMetaclassConflictingInstanceVars`) shows mypy treats it as a deliberate case.
Duplicates: one GitHub search (`metaclass instance variable class access`) returned 4 hits, the visible one being the feature overview #1889. No clear duplicate. Earlier notes cite #384 and #2815 as non-matches. I did not search closed issues exhaustively, nor python/typing discussions, nor ty releases above 0.0.84.

Verdict: ASK AS QUESTION (discussion, not bug), low priority.

Draft text:
> Title: Class access of a declared-only attribute shadows a metaclass attribute
> ```python
> from typing import ClassVar
> class Meta(type):
>     eggs: ClassVar[int] = 42
> class Foo(metaclass=Meta):
>     eggs: str
> reveal_type(Foo.eggs)  # ty: str; mypy: int; runtime: 42
> ```
> At runtime `Foo.eggs` resolves via the metaclass, since a bare annotation creates no class attribute. Is `str` the intended result for class-object access to a declared-only instance variable here? Related: mypy test testMetaclassConflictingInstanceVars.

## Recommendations
1. Fix harvester to honor mdtest python-version (removes lead b and likely similar noise).
2. Optionally post lead (a) as a question after a closed-issue search.
