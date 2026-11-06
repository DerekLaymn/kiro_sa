from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


bad: Config = {"name": "a", "extra": 1}
