from dataclasses import dataclass


@dataclass(kw_only=True)
class Config:
    retries: int = 3
    name: str
    debug: bool = False


def positional() -> None:
    Config('svc')


@dataclass(kw_only=True)
class C2:
    name: str


C2('svc')
