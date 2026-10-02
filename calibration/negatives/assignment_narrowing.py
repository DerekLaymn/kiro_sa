from typing import Optional, reveal_type


def run() -> None:
    maybe: Optional[int] = None
    reveal_type(maybe)
    value: int | str = 5
    reveal_type(value)


run()
