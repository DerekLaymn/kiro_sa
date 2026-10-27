from typing import Any, reveal_type


class Meta(type):
    def __getitem__(cls, idx: int) -> str:
        return f"{cls.__name__}[{idx}]"


class K(metaclass=Meta):
    pass


reveal_type(K[3])
print(K[3])
try:
    print(K["a"])  # type: ignore
except Exception as e:
    print(type(e).__name__)
reveal_type(len(K[0]))
