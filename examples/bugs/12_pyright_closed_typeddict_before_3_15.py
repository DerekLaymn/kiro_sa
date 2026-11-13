# Bug 12 (pyright): see examples/bugs/README.md for the issue link and the expected/actual result.
from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


bad: Config = {"name": "a", "extra": 1}
