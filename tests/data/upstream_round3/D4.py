class N[Z]: ...


class C[X](N[N["C[C[X]]"]]): ...


_: N[C[int]] = C[int]()
