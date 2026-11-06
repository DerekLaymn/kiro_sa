import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


both = F.R | F.W
reveal_type(both)
reveal_type(F.R | F.W)
reveal_type(~F.R)
reveal_type(F.R & F.W)
