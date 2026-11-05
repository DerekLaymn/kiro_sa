from typing import reveal_type


class Foo[*Ts, **P = [float, bool]]: ...


reveal_type(Foo[int, str]())
reveal_type(Foo[int, str, [bytes]]())
reveal_type(Foo[()]())
reveal_type(Foo())
