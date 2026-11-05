from typing import Callable

try:
    class Callback[*Ts, **P = [bool]]:
        fn: Callable[P, tuple[*Ts]]

    print(Callback[int, str].__name__)
except TypeError as e:
    print('TypeError:', e)
