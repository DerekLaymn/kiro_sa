from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


cfg: Config = {"name": "a"}
bad: Config = {"name": "a", "extra": 1}
print(cfg)
