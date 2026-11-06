# area: typeddict
# hypothesis: A closed TypedDict with a ReadOnly key, a NotRequired key and a Literal-typed key rejects undeclared keys and bad literal values, and checkers narrow the Literal value type while CPython stores plain dicts.
# origin: runs/day10/parents/N_types/hv_typeddict__pyright__typedDict10.py
# hypothesis: A closed TypedDict with a ReadOnly key, a NotRequired key and a Literal-typed key rejects undeclared keys and bad literal values, and checkers narrow the Literal value type while CPython stores plain dicts.
from typing import Literal, NotRequired, ReadOnly, TypedDict, Unpack, assert_type, reveal_type


class Config(TypedDict, closed=True):
    name: ReadOnly[str]
    retries: NotRequired[int]
    mode: Literal['fast', 'safe']


def describe(cfg: Config) -> str:
    return cfg['name'] + ':' + str(cfg.get('retries', 0)) + ':' + cfg['mode']


def build(**kwargs: Unpack[Config]) -> Config:
    return kwargs


def rename(cfg: Config) -> None:
    cfg['name'] = 'renamed'  # expect-error


def reject_extra() -> int:
    extra: Config = {'name': 'gamma', 'mode': 'fast', 'extra': 1}  # expect-error
    return len(extra)


def reject_mode() -> str:
    bad: Config = {'name': 'delta', 'mode': 'turbo'}  # expect-error
    return bad['name']


a: Config = {'name': 'alpha', 'mode': 'fast'}
b = build(name='beta', retries=2, mode='safe')
reveal_type(b['mode'])
assert_type(b['mode'], Literal['fast', 'safe'])
assert describe(a) == 'alpha:0:fast'
assert describe(b) == 'beta:2:safe'
assert reject_extra() == 3
assert reject_mode() == 'delta'
rename(a)
assert a['name'] == 'renamed'
