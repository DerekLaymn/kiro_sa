from typing import TypedDict


class Config(TypedDict, extra_items=int):
    name: str


print(Config)
