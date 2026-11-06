from typing import TypedDict


class Config(TypedDict, total=False, closed=True):
    name: str


print(Config)
