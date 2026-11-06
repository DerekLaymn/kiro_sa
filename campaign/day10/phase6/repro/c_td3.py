from typing_extensions import TypedDict


class Config(TypedDict, closed=True):
    name: str


c: Config = {"name": "a"}
print(c)
