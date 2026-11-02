from typing import Callable, Concatenate
type RecursiveParamspec[**P] = Callable[[], RecursiveParamspec[Concatenate[int, P]]]
