# Hypothesis: every discrepancy in this file is a DOCUMENTED divergence; the deterministic stage
# should dismiss all of them with a KB citation and send nothing to the LLM.
from typing import Callable, Optional, reveal_type


def split_paths(paths: str) -> list[str]:
    paths: list[str] = paths.split(":")  # ty redeclaration (mypy: no-redef)
    return paths


def name_of(c: Callable[[int], str]) -> str:
    return c.__name__  # ty: Callable has no __name__ (documented FAQ)


def to_str(x: int) -> str:
    return str(x)


mixed = [1, "a"]
reveal_type(mixed)  # mypy joins (list[object]), ty unions (list[int | str])

count = 3
reveal_type(count)  # mypy int, ty Literal[3]

maybe: Optional[int] = None
reveal_type(maybe)  # ty narrows on assignment, mypy shows the declared type

print(split_paths("a:b"), name_of(to_str))
